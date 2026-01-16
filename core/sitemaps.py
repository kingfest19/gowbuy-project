from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category, Service, ServiceCategory, Vendor, BlogPost

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return [
            'core:home',
            'core:sell_on_nexus',
            'core:become_service_provider',
            'core:become_rider_info_page',
            'authapp:signin',
            'authapp:signup',
            'core:daily_offers',
            'help',
            'terms',
            'privacy',
        ]

    def location(self, item):
        return reverse(item)

class ProductSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', obj.created_at)

class BlogSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return BlogPost.objects.filter(is_active=True)

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', obj.created_at)

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)

class ServiceSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Service.objects.filter(is_active=True)

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', obj.created_at)

class ServiceCategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return ServiceCategory.objects.filter(is_active=True)

class VendorSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Vendor.objects.filter(is_approved=True, is_verified=True)

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', obj.created_at)