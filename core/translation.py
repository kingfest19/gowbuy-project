from modeltranslation.translator import translator, TranslationOptions
from .models import Product, Service, ServiceCategory, ServicePackage


class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


class ServiceTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


class ServiceCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


class ServicePackageTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


translator.register(Product, ProductTranslationOptions)
translator.register(Service, ServiceTranslationOptions)
translator.register(ServiceCategory, ServiceCategoryTranslationOptions)
translator.register(ServicePackage, ServicePackageTranslationOptions)
