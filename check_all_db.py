#!/usr/bin/env python
import sqlite3

# Check raw product data
connection = sqlite3.connect('db.sqlite3')
cursor = connection.cursor()

print("=" * 80)
print("ALL Products in Database:")
print("=" * 80)
cursor.execute("SELECT id, name, name_en, name_ar FROM core_product ORDER BY id")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]:3} | name: '{row[1]:30}' | name_en: '{row[2]:30}' | name_ar: '{row[3]:30}'")

print("\n" + "=" * 80)
print("ALL Service Categories in Database:")
print("=" * 80)
cursor.execute("SELECT id, name, name_en, name_ar FROM core_servicecategory ORDER BY id")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]:3} | name: '{row[1]:30}' | name_en: '{row[2]:30}' | name_ar: '{row[3]:30}'")

connection.close()
