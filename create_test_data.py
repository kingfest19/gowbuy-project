#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Nexus.settings')
django.setup()

from core.models import Product, Service, ServiceCategory, ServicePackage, Category, Vendor
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a test vendor/user if needed
try:
    vendor = Vendor.objects.first()
    if not vendor:
        user = User.objects.first()
        if user:
            vendor = Vendor.objects.create(user=user, shop_name="Test Shop")
except:
    vendor = None

# Update existing products with test names and descriptions
products = Product.objects.all()
for i, product in enumerate(products, 1):
    product.name = f"Test Product {i}"
    product.description = f"This is a test product number {i} with some description."
    product.save()
    print(f"Updated Product {product.id}: {product.name}")

# Update existing services with test titles and descriptions
services = Service.objects.all()
for i, service in enumerate(services, 1):
    service.title = f"Test Service {i}"
    service.description = f"This is a test service number {i} with detailed description."
    service.save()
    print(f"Updated Service {service.id}: {service.title}")

# Update existing service categories with test names
categories = ServiceCategory.objects.all()
for i, category in enumerate(categories, 1):
    category.name = f"Category {i}"
    category.description = f"This is category {i} with some description."
    category.save()
    print(f"Updated Category {category.id}: {category.name}")

print("\nTest data created successfully!")
