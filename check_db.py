#!/usr/bin/env python
import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Nexus.settings')
django.setup()

from django.conf import settings

# Get the database connection
connection = sqlite3.connect('db.sqlite3')
cursor = connection.cursor()

# Check raw product data
print("=" * 80)
print("RAW DATABASE: core_product table")
print("=" * 80)
cursor.execute("PRAGMA table_info(core_product)")
columns = cursor.fetchall()
for col in columns[:15]:  # Show first 15 columns
    print(f"  {col[1]}: {col[2]}")

print("\nFirst 3 products:")
cursor.execute("SELECT id, name, name_en, name_ar, name_es FROM core_product LIMIT 3")
rows = cursor.fetchall()
for row in rows:
    print(f"  ID: {row[0]}, name: '{row[1]}', name_en: '{row[2]}', name_ar: '{row[3]}', name_es: '{row[4]}'")

print("\n" + "=" * 80)
print("RAW DATABASE: core_service table")
print("=" * 80)
cursor.execute("SELECT id, title, title_en, title_ar, title_es FROM core_service LIMIT 3")
rows = cursor.fetchall()
for row in rows:
    print(f"  ID: {row[0]}, title: '{row[1]}', title_en: '{row[2]}', title_ar: '{row[3]}', title_es: '{row[4]}'")

print("\n" + "=" * 80)
print("RAW DATABASE: core_servicecategory table")
print("=" * 80)
cursor.execute("SELECT id, name, name_en, name_ar, name_es FROM core_servicecategory LIMIT 3")
rows = cursor.fetchall()
for row in rows:
    print(f"  ID: {row[0]}, name: '{row[1]}', name_en: '{row[2]}', name_ar: '{row[3]}', name_es: '{row[4]}'")

connection.close()
