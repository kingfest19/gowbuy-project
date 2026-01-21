# c:\Users\Hp\Desktop\Nexus\core\management\commands\auto_translate.py
from django.core.management.base import BaseCommand
from django.conf import settings
import polib
import os
from deep_translator import GoogleTranslator

class Command(BaseCommand):
    help = 'Automatically translate .po files using Google Translate'

    def add_arguments(self, parser):
        parser.add_argument('lang_code', type=str, help='The language code to translate (e.g., es, fr, de)')

    def handle(self, *args, **options):
        lang_code = options['lang_code']
        
        # Adjust this path if your locale folder is in a different location
        locale_path = os.path.join(settings.BASE_DIR, 'locale')
        po_file_path = os.path.join(locale_path, lang_code, 'LC_MESSAGES', 'django.po')

        if not os.path.exists(po_file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {po_file_path}"))
            self.stdout.write(self.style.WARNING(f"Did you run 'django-admin makemessages -l {lang_code}' first?"))
            return

        self.stdout.write(f"Processing {po_file_path}...")
        
        try:
            po = polib.pofile(po_file_path, encoding='utf-8')
            # 'zh-hans' needs to be mapped to 'zh-CN' for Google Translate usually, 
            # but deep_translator handles many codes well.
            if lang_code.lower() in ['zh-hans', 'zh_hans']:
                target_lang = 'zh-CN'
            else:
                target_lang = lang_code
            
            translator = GoogleTranslator(source='auto', target=target_lang)
            
            translated_count = 0
            
            for entry in po:
                # Only translate if msgstr is empty and msgid is not empty
                if not entry.msgstr and entry.msgid:
                    try:
                        # Note: This simple translation might break Python format strings (e.g., %(value)s).
                        # For production, you should use regex to protect variables.
                        translation = translator.translate(entry.msgid)
                        if translation:
                            entry.msgstr = translation
                            translated_count += 1
                            self.stdout.write(f"Translated: '{entry.msgid}' -> '{translation}'")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Failed to translate '{entry.msgid}': {e}"))

            po.save()
            self.stdout.write(self.style.SUCCESS(f"Done! Translated {translated_count} entries."))
            self.stdout.write(self.style.SUCCESS("Now run: django-admin compilemessages"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
