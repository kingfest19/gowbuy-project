# core/filters.py
import django_filters
from .models import Product, Vendor, Category

class ProductFilter(django_filters.FilterSet):
    price = django_filters.RangeFilter()
    name = django_filters.CharFilter(lookup_expr='icontains', label='Product Name')
    vendor = django_filters.ModelChoiceFilter(queryset=Vendor.objects.filter(is_approved=True))
    is_sustainable = django_filters.BooleanFilter(field_name='vendor__is_sustainable_certified', label='Sustainable Certified Vendor')
    sustainability_tags = django_filters.CharFilter(lookup_expr='icontains', label='Sustainability Feature (e.g., organic)')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.filter(is_active=True))
    # You can add more filters for ratings, etc.

    class Meta:
        model = Product
        fields = ['price', 'name', 'vendor', 'category', 'is_sustainable', 'sustainability_tags']
