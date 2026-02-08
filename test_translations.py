#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Nexus.settings')
django.setup()

from core.models import Product, Service, ServiceCategory

print("=" * 60)
print("PRODUCTS")
print("=" * 60)
for p in Product.objects.all()[:3]:
    print(f"ID: {p.id}")
    print(f"  Original Name: {p.name}")
    print(f"  Name AR: {p.name_ar}")
    print(f"  Name ES: {p.name_es}")
    print(f"  Description (orig): {p.description[:50] if p.description else 'None'}")
    print(f"  Description AR: {p.description_ar[:50] if p.description_ar else 'None'}")
    print()

print("=" * 60)
print("SERVICES")
print("=" * 60)
for s in Service.objects.all()[:2]:
    print(f"ID: {s.id}")
    print(f"  Original Title: {s.title}")
    print(f"  Title AR: {s.title_ar}")
    print(f"  Title ES: {s.title_es}")
    print(f"  Description (orig): {s.description[:50] if s.description else 'None'}")
    print(f"  Description AR: {s.description_ar[:50] if s.description_ar else 'None'}")
    print()

print("=" * 60)
print("SERVICE CATEGORIES")
print("=" * 60)
for c in ServiceCategory.objects.all():
    print(f"ID: {c.id}")
    print(f"  Original Name: {c.name}")
    print(f"  Name AR: {c.name_ar}")
    print(f"  Name ES: {c.name_es}")
    print(f"  Description (orig): {c.description[:50] if c.description else 'None'}")
    print(f"  Description AR: {c.description_ar[:50] if c.description_ar else 'None'}")
    print()
