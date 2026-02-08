from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from core.models import Category
import json

# Nested mapping supports deeper category levels. Children can be a list (leaf names)
# or a dict (submapping of name -> children).
DEFAULT_MAPPING = {
    'Electronics': {
        'Phones': ['Smartphones', 'Feature Phones'],
        'Computers': ['Laptops', 'Desktops', 'Tablets'],
        'Audio': ['Headphones', 'Speakers'],
        'TVs & Home Cinema': [],
        'Cameras': ['DSLR', 'Mirrorless', 'Point & Shoot'],
        'Accessories': ['Chargers', 'Cables', 'Cases'],
    },
    'Fashion': {
        "Men's Clothing": ['Shirts', 'Trousers', 'Jackets'],
        "Women's Clothing": ['Dresses', 'Tops', 'Skirts'],
        'Kids': [],
        'Shoes': [],
        'Accessories': [],
        'Jewellery': [],
    },
    'Food': {
        'Groceries': ['Canned Goods', 'Dairy', 'Bakery'],
        'Beverages': ['Soft Drinks', 'Juices', 'Alcohol'],
        'Snacks': ['Chips', 'Confectionery'],
        'Fresh Produce': [],
        'Frozen Foods': [],
        'Condiments': [],
    },
    'Vehicles': {
        'Cars': ['Sedans', 'SUVs', 'Hatchbacks'],
        'Motorcycles': ['Cruisers', 'Sport', 'Scooters'],
        'Auto Parts': ['Engine Parts', 'Brakes', 'Tires'],
        'Accessories': [],
        'Car Care': [],
    },
    'Home & Garden': {
        'Furniture': ['Living Room', 'Bedroom', 'Storage'],
        'Kitchen': ['Cookware', 'Utensils', 'Appliances'],
        'Bedding': [],
        'Garden': [],
        'Decor': [],
    },
    'Beauty & Health': {
        'Skincare': ['Cleansers', 'Moisturizers'],
        'Makeup': [],
        'Personal Care': [],
        'Supplements': [],
    },
    'Sports & Outdoors': {
        'Fitness Equipment': [],
        'Outdoor Recreation': [],
        'Cycling': [],
        'Team Sports': [],
    },
    'Toys & Kids': {
        'Infant Toys': [],
        'Educational': [],
        'Puzzles & Games': [],
    },
}


def _ensure_category(name, parent=None, force=False):
    # If a category with the same name exists anywhere, consider it existing to avoid violating unique name constraint
    name_qs = Category.objects.filter(name__iexact=name)
    if name_qs.exists():
        return name_qs.first(), False

    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    # Ensure global uniqueness of slug (Category.slug is unique in DB)
    while Category.objects.filter(slug=slug).exists():
        # If a category with same slug exists and has same parent, treat as existing
        qs_same_parent = Category.objects.filter(parent=parent, slug=slug)
        if qs_same_parent.exists():
            cat = qs_same_parent.first()
            if force and cat.name != name:
                cat.name = name
                cat.is_active = True
                cat.save()
            return cat, False
        # Otherwise, modify slug to make it unique
        slug = f"{base_slug}-{counter}"
        counter += 1

    cat = Category.objects.create(name=name, slug=slug, parent=parent, is_active=True)
    return cat, True


def _process_node(parent, node, preview, created, skipped, force, actions):
    # node can be list or dict
    if isinstance(node, dict):
        for child_name, child_node in node.items():
            actions.append((parent, child_name))
            # Create or get the child category (unless preview)
            if preview:
                class Dummy:
                    def __init__(self, name):
                        self.name = name
                child_parent = Dummy(child_name)
            else:
                cat, was_created = _ensure_category(child_name, parent=parent, force=force)
                if was_created:
                    created.append((parent.name if parent else None, child_name))
                else:
                    skipped.append((parent.name if parent else None, child_name, 'exists'))
                child_parent = cat

            # Recurse into child node
            _process_node(child_parent, child_node, preview, created, skipped, force, actions)

    elif isinstance(node, list):
        for child_name in node:
            actions.append((parent, child_name))
            if preview:
                continue
            cat, was_created = _ensure_category(child_name, parent=parent, force=force)
            if was_created:
                created.append((parent.name if parent else None, child_name))
            else:
                skipped.append((parent.name if parent else None, child_name, 'exists'))
    else:
        # single name
        actions.append((parent, str(node)))
        if not preview:
            cat, was_created = _ensure_category(str(node), parent=parent, force=force)
            if was_created:
                created.append((parent.name if parent else None, str(node)))
            else:
                skipped.append((parent.name if parent else None, str(node), 'exists'))


class Command(BaseCommand):
    help = 'Populate common subcategories under top-level categories. Supports nested levels.'

    def add_arguments(self, parser):
        parser.add_argument('--preview', action='store_true', help='Show what would be created without making changes')
        parser.add_argument('--force', action='store_true', help='Force creation even if slugs collide')
        parser.add_argument('--create-top-level', action='store_true', help='Create missing top-level categories automatically')
        parser.add_argument('--mapping', type=str, help='Path to a JSON file with custom mapping (optional)')

    def handle(self, *args, **options):
        preview = options.get('preview')
        force = options.get('force')
        create_top = options.get('create_top_level') if options.get('create_top_level') is not None else options.get('create-top-level')

        mapping = DEFAULT_MAPPING
        if options.get('mapping'):
            path = options.get('mapping')
            with open(path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)

        created = []
        skipped = []
        warnings = []
        actions = []

        # Iterate top-level
        for top_name, node in mapping.items():
            try:
                top = Category.objects.get(name__iexact=top_name, parent__isnull=True)
                top_found = True
            except Category.DoesNotExist:
                top_found = False
                if create_top and not preview:
                    top, was_created = _ensure_category(top_name, parent=None, force=force)
                    if was_created:
                        created.append((None, top_name))
                else:
                    warnings.append(f"Top-level category '{top_name}' not found.")
            if not top_found and not create_top:
                continue
            if not top_found and preview:
                # Use dummy parent for preview naming
                class DummyTop:
                    def __init__(self, name):
                        self.name = name
                top = DummyTop(top_name)

            _process_node(top, node, preview, created, skipped, force, actions)

        # Print actions for preview
        if preview:
            for parent, child in actions:
                parent_name = parent.name if parent else 'ROOT'
                self.stdout.write(f"CREATE: '{child}' (parent='{parent_name}')")

        self.stdout.write('\nSummary:')
        if preview:
            self.stdout.write(self.style.NOTICE('Preview mode - no changes were made.'))
        self.stdout.write(self.style.SUCCESS(f'Created: {len(created)}'))
        if skipped:
            self.stdout.write(self.style.WARNING(f'Skipped: {len(skipped)} (already exist or collisions)'))
        if warnings:
            for w in warnings:
                self.stdout.write(self.style.WARNING(w))

        if not preview and created:
            self.stdout.write(self.style.SUCCESS('Subcategory creation complete.'))
        elif not preview and not created:
            self.stdout.write(self.style.NOTICE('No subcategories were created.'))
