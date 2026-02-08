from django.core.management.base import BaseCommand
from core.models import Product, Service, ServiceCategory, ServicePackage
from deep_translator import GoogleTranslator
import time


class Command(BaseCommand):
    help = 'Populate database fields with translations for products and services'

    def handle(self, *args, **options):
        def translate_text(text, target_lang):
            if not text:
                return text
            try:
                translator = GoogleTranslator(source='en', target=target_lang)
                return translator.translate(text)
            except Exception as e:
                self.stdout.write(f"Error translating to {target_lang}: {e}")
                time.sleep(1)
                return text

        # Translate products
        products = Product.objects.all()
        translated_count = 0
        for product in products:
            # Skip if already translated
            if product.name_zh_hans:
                continue
                
            # Get source text from original fields (which act as the 'default' language)
            source_name = product.name if product.name else ""
            source_desc = product.description if product.description else ""
            
            # Only translate if we have content
            if not source_name:
                continue

            # Set the _en fields first
            product.name_en = source_name
            product.description_en = source_desc
            
            # Then translate to other languages
            product.name_ar = translate_text(source_name, 'ar')
            product.name_es = translate_text(source_name, 'es')
            product.name_pt = translate_text(source_name, 'pt')
            product.name_zh_hans = translate_text(source_name, 'zh-CN')

            product.description_ar = translate_text(source_desc, 'ar')
            product.description_es = translate_text(source_desc, 'es')
            product.description_pt = translate_text(source_desc, 'pt')
            product.description_zh_hans = translate_text(source_desc, 'zh-CN')

            try:
                product.save(update_fields=['name_en', 'name_ar', 'name_es', 'name_pt', 'name_zh_hans',
                                           'description_en', 'description_ar', 'description_es', 'description_pt', 'description_zh_hans'])
                translated_count += 1
            except Exception as e:
                self.stdout.write(f"Warning: Could not save product {product.id}: {e}")
            
            time.sleep(0.3)

        self.stdout.write(f"Translated {translated_count} products")

        # Translate services
        services = Service.objects.all()
        translated_count = 0
        for service in services:
            # Skip if already translated
            if service.title_zh_hans:
                continue
                
            # Get source text from original fields
            source_title = service.title if service.title else ""
            source_desc = service.description if service.description else ""
            
            if not source_title:
                continue

            # Set the _en fields first
            service.title_en = source_title
            service.description_en = source_desc
            
            # Then translate to other languages
            service.title_ar = translate_text(source_title, 'ar')
            service.title_es = translate_text(source_title, 'es')
            service.title_pt = translate_text(source_title, 'pt')
            service.title_zh_hans = translate_text(source_title, 'zh-CN')

            service.description_ar = translate_text(source_desc, 'ar')
            service.description_es = translate_text(source_desc, 'es')
            service.description_pt = translate_text(source_desc, 'pt')
            service.description_zh_hans = translate_text(source_desc, 'zh-CN')

            try:
                service.save(update_fields=['title_en', 'title_ar', 'title_es', 'title_pt', 'title_zh_hans',
                                           'description_en', 'description_ar', 'description_es', 'description_pt', 'description_zh_hans'])
                translated_count += 1
            except Exception as e:
                self.stdout.write(f"Warning: Could not save service {service.id}: {e}")
            
            time.sleep(0.3)

        self.stdout.write(f"Translated {translated_count} services")

        # Translate service categories
        categories = ServiceCategory.objects.all()
        translated_count = 0
        for cat in categories:
            # Skip if already translated
            if cat.name_zh_hans:
                continue
                
            # Get source text from original fields
            source_name = cat.name if cat.name else ""
            source_desc = cat.description if cat.description else ""
            
            if not source_name:
                continue

            # Set the _en fields first
            cat.name_en = source_name
            cat.description_en = source_desc
            
            # Then translate to other languages
            cat.name_ar = translate_text(source_name, 'ar')
            cat.name_es = translate_text(source_name, 'es')
            cat.name_pt = translate_text(source_name, 'pt')
            cat.name_zh_hans = translate_text(source_name, 'zh-CN')

            if source_desc:
                cat.description_ar = translate_text(source_desc, 'ar')
                cat.description_es = translate_text(source_desc, 'es')
                cat.description_pt = translate_text(source_desc, 'pt')
                cat.description_zh_hans = translate_text(source_desc, 'zh-CN')

            try:
                cat.save(update_fields=['name_en', 'name_ar', 'name_es', 'name_pt', 'name_zh_hans',
                                       'description_en', 'description_ar', 'description_es', 'description_pt', 'description_zh_hans'])
                translated_count += 1
            except Exception as e:
                self.stdout.write(f"Warning: Could not save category {cat.id}: {e}")
            
            time.sleep(0.3)

        self.stdout.write(f"Translated {translated_count} service categories")

        # Translate service packages
        packages = ServicePackage.objects.all()
        translated_count = 0
        for pkg in packages:
            # Skip if already translated
            if pkg.name_zh_hans:
                continue
                
            # Get source text from original fields
            source_name = pkg.name if pkg.name else ""
            source_desc = pkg.description if pkg.description else ""
            
            if not source_name:
                continue

            # Set the _en fields first
            pkg.name_en = source_name
            pkg.description_en = source_desc
            
            # Then translate to other languages
            pkg.name_ar = translate_text(source_name, 'ar')
            pkg.name_es = translate_text(source_name, 'es')
            pkg.name_pt = translate_text(source_name, 'pt')
            pkg.name_zh_hans = translate_text(source_name, 'zh-CN')

            pkg.description_ar = translate_text(source_desc, 'ar')
            pkg.description_es = translate_text(source_desc, 'es')
            pkg.description_pt = translate_text(source_desc, 'pt')
            pkg.description_zh_hans = translate_text(source_desc, 'zh-CN')

            try:
                pkg.save(update_fields=['name_en', 'name_ar', 'name_es', 'name_pt', 'name_zh_hans',
                                       'description_en', 'description_ar', 'description_es', 'description_pt', 'description_zh_hans'])
                translated_count += 1
            except Exception as e:
                self.stdout.write(f"Warning: Could not save package {pkg.id}: {e}")
            
            time.sleep(0.3)

        self.stdout.write(f"Translated {translated_count} service packages")
        self.stdout.write(self.style.SUCCESS("All database content translated successfully!"))
