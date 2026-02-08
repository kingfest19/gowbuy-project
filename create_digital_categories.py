#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Nexus.settings')
django.setup()

from core.models import Category

# Digital Products Parent Category
digital_parent, created = Category.objects.update_or_create(
    name='Digital Products',
    defaults={
        'description': 'Digital products and files available for download',
        'is_active': True
    }
)
print(f"Digital Products parent: {digital_parent.name} (created={created})")

# Digital subcategories
digital_categories = [
    'eBooks & Documents',
    'Software & Applications',
    'Online Courses',
    'Templates & Designs',
    'Music & Audio',
    'Videos & Animation',
    'Plugins & Extensions',
    'Graphics & Icons',
    'Writing & Storytelling',
    'Photography & Images',
]

for cat_name in digital_categories:
    cat, created = Category.objects.update_or_create(
        name=cat_name,
        defaults={
            'parent': digital_parent,
            'description': f'{cat_name} digital products',
            'is_active': True
        }
    )
    print(f"  - {cat_name} (created={created})")

print("\nAll Digital Categories:")
for cat in digital_parent.subcategories.all():
    print(f"  {cat.name}")
