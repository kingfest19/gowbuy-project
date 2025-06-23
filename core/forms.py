# c:\Users\Hp\Desktop\Nexus\core\forms.py
from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML, Field
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import logging # <<< Add this import
# Import models needed for forms
from .utils import geocode_address # Import the new utility
from decimal import Decimal # Ensure Decimal is imported
from .models import (
    VendorReview, ProductReview, Vendor, Promotion, AdCampaign, Product, Category, ServiceProviderProfile, PortfolioItem,
    ServiceCategory, Service, ServiceReview, ServicePackage, Address, VendorShipping, VendorPayment, VendorAdditionalInfo, PayoutRequest, # Added PayoutRequest
    RiderProfile, RiderApplication, DeliveryTask
)
from django.contrib.auth import get_user_model

class VendorReviewForm(forms.ModelForm):
    """
    Form for submitting a review for a Vendor.
    """
    class Meta:
        model = VendorReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Share your experience with this vendor...'}),
        }
        labels = {
            'rating': 'Your Rating',
            'comment': 'Your Review (Optional)',
        }

# --- ProductReviewForm ---
class ProductReviewForm(forms.ModelForm):
    """
    Form for submitting a review for a Product.
    """
    class Meta:
        model = ProductReview
        fields = ['rating', 'review', 'video']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'review': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Share your thoughts on this product...'}),
            'video': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'rating': 'Your Rating*',
            'review': 'Your Review',
            'video': 'Upload Video (Optional)',
        }
        help_texts = {
            'video': 'Upload a short video showing the product (MP4, WebM recommended).'
        }
# --- End ProductReviewForm ---

# --- VendorRegistrationForm ---
class VendorRegistrationForm(forms.ModelForm):
    """
    Form for users to apply to become vendors. Simplified for initial registration.
    Verification details will be collected later.
    """
    class Meta:
        model = Vendor
        fields = ['name', 'contact_email', 'phone_number', 'description', 'logo']

        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Briefly describe your business and the products you sell...'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'placeholder': 'Your Business Name'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'Business Contact Email'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Business Phone Number'}),
        }

# --- End VendorRegistrationForm ---

# --- START: Multi-Step Vendor Verification Forms ---

class VerificationMethodSelectionForm(forms.Form):
    verification_method = forms.ChoiceField(
        choices=Vendor.VERIFICATION_METHOD_CHOICES,
        widget=forms.RadioSelect,
        label=_("How are you registering?"),
        required=True,
        help_text=_("Select the method you will use for verification.")
    )

class BusinessDetailsForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'business_registration_document',
            'tax_id_number',
            'other_supporting_document',
        ]
        widgets = {
            'business_registration_document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'tax_id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter your Business TIN')}),
            'other_supporting_document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'business_registration_document': _("Business Registration Document"),
            'tax_id_number': _("Tax Identification Number (TIN)"),
            'other_supporting_document': _("Other Supporting Document (Optional)"),
        }
        help_texts = {
            'business_registration_document': _("e.g., Business Registration Certificate, Certificate of Incorporation."),
            'other_supporting_document': _("Any other supporting document for business verification."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For this step, these are considered required if this form is presented.
        self.fields['business_registration_document'].required = True
        self.fields['tax_id_number'].required = True
        self.fields['other_supporting_document'].required = False # This one is truly optional


class IndividualDetailsForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'national_id_type',
            'national_id_number',
            'national_id_document',
        ]
        widgets = {
            'national_id_type': forms.Select(
                attrs={'class': 'form-select'},
                choices=[ # Ensure choices are tuples of (value, label)
                    ('', '---------'),
                    ('National ID Card', _('National ID Card')),
                    ('Passport', _('Passport')),
                    ('Driver\'s License', _('Driver\'s License')),
                    ('Voter ID', _('Voter ID')),
                ]
            ),
            'national_id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter ID Number')}),
            'national_id_document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'national_id_type': _("Type of National ID"),
            'national_id_number': _("National ID Number"),
            'national_id_document': _("National ID Document"),
        }
        help_texts = {
            'national_id_document': _("Scanned copy of the National ID document."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For this step, these are considered required if this form is presented.
        self.fields['national_id_type'].required = True
        self.fields['national_id_number'].required = True
        self.fields['national_id_document'].required = True


class VerificationConfirmationForm(forms.Form):
    agree_to_terms = forms.BooleanField(
        label=_("I confirm the provided information is accurate and agree to the Vendor Terms and Conditions"),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

# --- END: Multi-Step Vendor Verification Forms ---
 
# --- VendorProfileUpdateForm ---
class VendorProfileUpdateForm(forms.ModelForm):
    """
    Form for vendors to update their public profile information.
    """
    class Meta:
        model = Vendor
        fields = [
            'name', 'description', 'contact_email', 'phone_number',
            'logo', 'location_city', 'location_country', 'shipping_policy', 'return_policy',
            'public_phone_number', 'public_email', 'website_url',
            'facebook_url', 'instagram_url', 'twitter_url', 'linkedin_url', 'whatsapp_number'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Business Name'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Describe your business and products...'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Business Contact Email'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Business Phone Number'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'location_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'location_country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'shipping_policy': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Describe your shipping policy...'}),
            'return_policy': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Describe your return policy...'}),
            'public_phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g., +1234567890')}),
            'public_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('public@example.com')}),
            'website_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://yourwebsite.com')}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://facebook.com/yourpage')}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://instagram.com/yourprofile')}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://twitter.com/yourhandle')}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://linkedin.com/in/yourprofile')}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('+12345678900')}),
        }
        # Note: latitude and longitude fields are not included here as they are auto-generated
        labels = {
            'contact_email': _("Primary Contact Email (Private)"),
            'phone_number': _("Primary Contact Phone (Private)"),
            'public_phone_number': _("Publicly Displayed Phone Number"),
            'public_email': _("Publicly Displayed Email Address"),
            'website_url': _("Your Website URL"),
            'facebook_url': _("Facebook Page URL"),
            'instagram_url': _("Instagram Profile URL"),
            'twitter_url': _("Twitter (X) Profile URL"),
            'linkedin_url': _("LinkedIn Profile URL"),
            'whatsapp_number': _("Public WhatsApp Number"),
        }
        help_texts = {
            'whatsapp_number': _("Enter with country code. This will be visible to customers."),
        }

    def __init__(self, *args, **kwargs): # Add __init__ if not present
        super().__init__(*args, **kwargs)
        # Make fields optional if they are in the model
        optional_fields = [
            'description', 'contact_email', 'phone_number', 'logo',
            'street_address', 'location_city', 'location_country',
            'shipping_policy', 'return_policy',
            'public_phone_number', 'public_email', 'website_url',
            'facebook_url', 'instagram_url', 'twitter_url', 'linkedin_url', 'whatsapp_number'
        ]
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False


    def save(self, commit=True):
        instance = super().save(commit=False)

        street = self.cleaned_data.get('street_address')
        city = self.cleaned_data.get('location_city')
        country = self.cleaned_data.get('location_country')

        address_parts = [part for part in [street, city, country] if part] # Filter out None or empty strings
        address_string_for_geocoding = ", ".join(address_parts)

        # Determine if geocoding is needed:
        # 1. If any of the address components (street, city, country) have changed.
        # 2. OR if latitude or longitude is currently missing AND we have an address string to geocode.
        address_fields_changed = any(field in self.changed_data for field in ['street_address', 'location_city', 'location_country'])

        needs_geocoding = False
        if address_string_for_geocoding: # Only if we have something to geocode
            if address_fields_changed:
                needs_geocoding = True
            elif instance.latitude is None or instance.longitude is None:
                needs_geocoding = True

        if needs_geocoding:
            logging.info(f"Attempting to geocode address for vendor '{instance.name}': {address_string_for_geocoding}")
            lat, lng = geocode_address(address_string_for_geocoding)
            if lat is not None and lng is not None:
                instance.latitude = lat
                instance.longitude = lng
                logging.info(f"Geocoding successful for vendor '{instance.name}'. Lat: {lat}, Lng: {lng}")
            else:
                # If geocoding fails, clear existing coordinates to avoid using stale data
                # for a potentially new address.
                instance.latitude = None
                # Add a non-field error to the form to inform the user
                # self.add_error(None, _("Could not determine precise map coordinates from the address provided. Please check the address details (Street, City, Country) or contact support if the issue persists."))
                # Note: We don't clear longitude here yet, it will be cleared below if lat is None
                instance.longitude = None
                logging.warning(f"Geocoding failed for vendor '{instance.name}'. Coordinates cleared.")
        elif not address_string_for_geocoding and (instance.latitude is not None or instance.longitude is not None):
            # If all address parts are cleared, clear coordinates too
            logging.info(f"Address fields cleared for vendor '{instance.name}'. Clearing coordinates.")
            instance.latitude = None
            instance.longitude = None

        if commit:
            instance.save()
        return instance

# --- End VendorProfileUpdateForm ---

# --- VendorShippingForm ---
class VendorShippingForm(forms.ModelForm):
    """
    Form for vendors to update their shipping policy.
    """
    class Meta:
        model = Vendor
        fields = ['shipping_policy']
        widgets = {
            'shipping_policy': forms.Textarea(attrs={'rows': 8, 'class': 'form-control', 'placeholder': _('Describe your shipping methods, costs, delivery times, and regions you ship to...')}),
        }
        labels = {
            'shipping_policy': _('Your Shipping Policy Details'),
        }

# --- End VendorShippingForm ---

# --- VendorPaymentForm ---
class VendorPaymentForm(forms.ModelForm):
    """
    Form for vendors to update their payment information (e.e., Mobile Money).
    """
    PROVIDER_CHOICES = (('', '---------'), ('MTN', 'MTN Mobile Money'), ('Vodafone', 'Vodafone Cash'), ('AirtelTigo', 'AirtelTigo Money'))
    mobile_money_provider = forms.ChoiceField(choices=PROVIDER_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Vendor
        fields = ['mobile_money_provider', 'mobile_money_number']
        widgets = {
            'mobile_money_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter your Mobile Money number')}),
        }
# --- End VendorPaymentForm ---

# --- PromotionForm ---
class PromotionForm(forms.ModelForm):
    """
    Form for vendors/admins to create or update promotions.
    """
    start_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    end_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))

    applicable_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text=_("Select categories if scope is 'Specific Category'.")
    )
    applicable_products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text=_("Select products if scope is 'Specific Product(s)'.")
    )

    class Meta:
        model = Promotion
        exclude = ['vendor', 'current_uses', 'created_at', 'applicable_vendor']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Optional coupon code')}),
            'promo_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'scope': forms.Select(attrs={'class': 'form-select'}),
            'min_purchase_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_uses': forms.NumberInput(attrs={'class': 'form-control'}),
            'uses_per_customer': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)
        if vendor:
            self.fields['applicable_products'].queryset = Product.objects.filter(vendor=vendor, is_active=True)

# --- End PromotionForm ---

# --- AdCampaignForm ---
class AdCampaignForm(forms.ModelForm):
    """
    Form for vendors to create or update ad campaigns.
    """
    start_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    end_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    promoted_product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text=_("Select a product to promote, or leave blank to promote your store.")
    )

    class Meta:
        model = AdCampaign
        exclude = ['vendor', 'created_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'placement': forms.Select(attrs={'class': 'form-select'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)
        if vendor:
            self.fields['promoted_product'].queryset = Product.objects.filter(vendor=vendor, is_active=True)

# --- End AdCampaignForm ---

# --- VendorProductForm ---
class VendorProductForm(forms.ModelForm):
    """
    Form for vendors to add or edit their products.
    """
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Product
        fields = [
            'product_type', 'fulfillment_method', 'vendor_delivery_fee',
            'category', 'name', 'description', 'keywords_for_ai', 'price', # Added keywords_for_ai
            'stock', 'digital_file', 'three_d_model', # Added three_d_model
            'is_active', 'is_featured',
        ]
        widgets = {
            'fulfillment_method': forms.Select(attrs={'class': 'form-select'}),
            'vendor_delivery_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': _('e.g., 5.00')}),
            'product_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'keywords_for_ai': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g., durable, eco-friendly, best gift')}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'digital_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'three_d_model': forms.ClearableFileInput(attrs={'class': 'form-control'}), # Added widget for consistency
        }
        help_texts = {
            'fulfillment_method': _("Choose how this specific product will be fulfilled. If left blank, your store's default fulfillment method will be used."),
            'vendor_delivery_fee': _("If you fulfill this product yourself ('Fulfilled by Vendor'), set your delivery fee here. Leave as 0.00 if delivery is free or included in product price, or if Nexus fulfills."),
            'keywords_for_ai': _("Optional: Comma-separated keywords to guide AI description generation."),
            'three_d_model': _("Upload a 3D model file (e.g., .glb, .gltf) for 3D viewing."),
        }
    def __init__(self, *args, **kwargs): # Ensure blank option for fulfillment_method
        super().__init__(*args, **kwargs)
        self.fields['fulfillment_method'].choices = [('', _("Use Vendor Default"))] + list(Vendor.FULFILLMENT_CHOICES)
# --- End VendorProductForm ---

# --- Vendor Additional Information Form ---
class VendorAdditionalInfoForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['return_policy']
        widgets = {
            'return_policy': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }




# --- START: Service Marketplace Forms ---

class ServiceForm(forms.ModelForm):
    """
    Form for creating and editing services.
    """
    category = forms.ModelChoiceField(
        queryset=ServiceCategory.objects.filter(is_active=True).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Service Category"),
        empty_label=_("Select a Category...")
    )

    class Meta:
        model = Service
        fields = [
            'category', 'title', 'description', 'is_featured',
             'skills', 'experience', 'education',
            'location', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g., Professional Logo Design')}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': _('Describe the service you offer in detail...')}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.e., Accra, Remote, Nationwide')}),
            'skills': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': _('e.g., Python, Graphic Design, Copywriting')}),
            'experience': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': _('e.g., 5 years experience in web development...')}),
            'education': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': _('e.g., BSc Computer Science, Google Certified...')}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': _('Service Title'),
            'description': _('Detailed Description'),
            'location': _('Service Location'),
            'is_active': _("Make this service listing active?"),
            'skills': _('Skills'),
            'experience': _('Experience Summary'),
            'education': _('Education / Certifications'),
            'is_featured': _("Feature this service?"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('category', css_class='mb-3'),
            Field('title', css_class='mb-3'),
            Field('description', css_class='mb-3'),
            Fieldset(_('Your Qualifications (Optional)'),
                Field('skills', css_class='mb-3'),
                Field('experience', css_class='mb-3'),
                Field('education', css_class='mb-3'),
                css_class='border p-3 rounded mb-3'
            ),
            Field('location', css_class='mb-3'),
            Field('is_active', css_class='mb-3'),
            Field('is_featured', css_class='mb-3')
        )

# --- START: Service Package Form (Standalone Class) ---
class ServicePackageForm(forms.ModelForm):
    """Form for individual service packages within the formset."""
    class Meta:
        model = ServicePackage
        fields = ('name', 'description', 'price', 'delivery_time', 'revisions', 'display_order', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': _('Package Name')}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2, 'placeholder': _('Package Description')}),
            'price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'delivery_time': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'revisions': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Field('name', css_class='mb-3'),
            Field('price', css_class='mb-3'),
            Field('description', css_class='mb-3'),
            Field('delivery_time', css_class='mb-3'),
            Field('revisions', css_class='mb-3'),
            Field('display_order', css_class='mb-3'),
            Fieldset(
                '',
                'is_active',
                css_class='mt-2'
            )
        )
# --- END: Service Package Form ---

# --- START: Service Package Formset ---
ServicePackageFormSet = inlineformset_factory(
    Service,
    ServicePackage,
    form=ServicePackageForm,
    extra=1,
    can_delete=True,
)
# --- END: Service Package Formset ---

# --- START: Service Review Form ---
class ServiceReviewForm(forms.ModelForm):
    """
    Form for submitting a review for a Service.
    """
    class Meta:
        model = ServiceReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': _('Share your experience with this service...')}),
        }
        labels = {
            'rating': _('Your Rating'),
            'comment': _('Your Review (Optional)'),
        }
# --- END: Service Review Form ---

# --- START: Service Search Form ---
class ServiceSearchForm(forms.Form):
    """
    Simple form for searching services.
    """
    q = forms.CharField(label=_("Search Services"), required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Search Services')}))
# --- END: Service Search Form ---

# --- START: Address Form ---
class AddressForm(forms.ModelForm):
    """
    Form for creating and updating user addresses.
    """
    class Meta:
        model = Address
        fields = [
            'address_type', 'full_name', 'street_address', 'apartment_address',
            'city', 'state', 'zip_code', 'country', 'phone_number', 'is_default'
        ]
        widgets = {
            'address_type': forms.Select(attrs={'class': 'form-select'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Recipient's Full Name")}),
            'street_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Street Address")}),
            'apartment_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Apt, suite, unit, etc. (Optional)")}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("City")}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("State / Province / Region")}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("ZIP / Postal Code")}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Country")}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Phone Number (Optional)")}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['apartment_address', 'phone_number', 'is_default']:
                field.required = False

        if 'address_type' in self.fields:
            self.fields['address_type'].required = False
# --- END: Address Form ---

    # Add user as an argument
    def save(self, commit=True, user=None):
        instance = super().save(commit=False)

        # Gather address components for geocoding
        street = self.cleaned_data.get('street_address')
        city = self.cleaned_data.get('city')
        state = self.cleaned_data.get('state') # State can also be useful
        country = self.cleaned_data.get('country')
        zip_code = self.cleaned_data.get('zip_code') # Zip code can also be useful

        # Construct a comprehensive address string
        address_parts = [part for part in [street, city, state, zip_code, country] if part]
        address_string_for_geocoding = ", ".join(address_parts)

        # Determine if geocoding is needed
        address_fields_changed = any(field in self.changed_data for field in ['street_address', 'city', 'state', 'zip_code', 'country'])

        needs_geocoding = False
        if address_string_for_geocoding: # Only if we have something to geocode
            if address_fields_changed:
                needs_geocoding = True
            elif instance.latitude is None or instance.longitude is None: # If coords are missing
                needs_geocoding = True

        if needs_geocoding:
            # Use the passed-in user for logging. instance.user is not yet set here.
            logging.info(f"Attempting to geocode address for user '{user.username if user else 'Unknown User'}' (address type: '{instance.address_type}'): {address_string_for_geocoding}")
            lat, lng = geocode_address(address_string_for_geocoding)
            if lat is not None and lng is not None:
                instance.latitude = lat
                instance.longitude = lng
                logging.info(f"Geocoding successful for address. Lat: {lat}, Lng: {lng}")
            else:
                # If geocoding fails, clear existing coordinates to avoid using stale data
                instance.latitude = None
                instance.longitude = None
                logging.warning(f"Geocoding failed for address. Coordinates cleared.")
                # Optionally, add a non-field error if this form were displayed directly with errors
                # self.add_error(None, _("Could not determine map coordinates from the address provided. Please check the details."))

        if commit:
            instance.save()
        return instance

# --- START: Service Provider Registration Form ---
class ServiceProviderRegistrationForm(forms.ModelForm):
    class Meta:
        model = ServiceProviderProfile
        fields = [
            'business_name', 'bio',
            'payout_mobile_money_provider', 'payout_mobile_money_number'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 5}),
            'payout_mobile_money_provider': forms.Select(attrs={'class': 'form-select'}),
            'payout_mobile_money_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g., 024xxxxxxx')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['business_name'].widget.attrs.update({'class': 'form-control', 'placeholder': _('e.g., Your Awesome Services Inc.')})
        self.fields['bio'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Tell us about the services you offer, your experience, and what makes you stand out...')})
        self.fields['payout_mobile_money_provider'].required = False
        self.fields['payout_mobile_money_number'].required = False
        self.fields['payout_mobile_money_number'].help_text = _("Ensure this number is registered for Mobile Money and can receive payments.")

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

# --- END: Service Provider Registration Form ---

# --- START: Rider Forms ---
class RiderProfileApplicationForm(forms.ModelForm):
    agreed_to_terms = forms.BooleanField(
        required=True,
        label=_("I agree to the Rider Terms and Conditions and Privacy Policy."),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    class Meta:
        model = RiderApplication
        fields = [
            'phone_number',
            'vehicle_type',
            'vehicle_registration_number',
            'license_number',
            'address',
            'vehicle_registration_document',
            'drivers_license_front',
            'drivers_license_back',
            'id_card_front',
            'id_card_back',
            'profile_picture',
            'vehicle_picture', # New
            'agreed_to_terms'
        ]

        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g., 024xxxxxxx')}),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'vehicle_registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g., GR 1234-23')}),
            'license_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g., YourDriverLicense123')}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': _('e.g., Accra Central, Kumasi Metropolis')}),
            'vehicle_registration_document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'drivers_license_front': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'drivers_license_back': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'id_card_front': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'id_card_back': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'vehicle_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}), # New
        }

        help_texts = {
            'phone_number': _("We'll use this to contact you for deliveries."),
            'address': _("The general area or city you'll be operating in."),
            'license_number': _("Your driver's license number."),
            'vehicle_registration_document': _("Upload a clear image of your vehicle's registration document."),
            'drivers_license_front': _("Upload the front of your driver's license."),
            'drivers_license_back': _("Upload the back of your driver's license."),
            'id_card_front': _("Upload the front of your National ID card (e.g., Ghana Card)."),
            'id_card_back': _("Upload the back of your National ID card."),
            'profile_picture': _("A clear, recent photo of yourself."),
            'vehicle_picture': _("Upload a clear picture of your delivery vehicle (showing registration plate if possible)."), # New
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        optional_fields = [
            'vehicle_registration_document', # This can remain optional if you wish, or remove if it should be required
            'id_card_front',
            'id_card_back',
            'profile_picture'
        ] # license_number, its docs, vehicle_registration_number, and vehicle_picture are now required by model
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

# --- END: Rider Forms ---


# --- START: Rider Profile Update Form ---
class RiderProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, label=_("First Name"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=False, label=_("Last Name"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    profile_picture = forms.ImageField(required=False, label=_("Profile Picture"), widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = RiderProfile
        fields = [
            'phone_number', 'vehicle_type', 'vehicle_registration_number', 'license_number', 'address',
            'current_vehicle_registration_document',
            'current_drivers_license_front', 'current_drivers_license_back',
            'current_id_card_front', 'current_id_card_back',
            'current_vehicle_picture'
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g., +1234567890')}),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'vehicle_registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g., GR 1234-23')}),
            'license_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Optional, e.g., YourDriverLicense123')}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': _('e.g., Accra Central, Kumasi Metropolis')}),
            # Widgets for the new document fields
            'current_vehicle_registration_document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'current_drivers_license_front': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'current_drivers_license_back': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'current_id_card_front': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'current_id_card_back': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'current_vehicle_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'phone_number': _("Phone Number"),
            'vehicle_type': _("Vehicle Type"),
            'vehicle_registration_number': _("Vehicle Registration Number"),
            'license_number': _("Driver's License Number"),
            'address': _("Operating Address / Area"),
            # Labels for new document fields
            'current_vehicle_registration_document': _("Update Vehicle Registration Document"),
            'current_drivers_license_front': _("Update Driver's License (Front)"),
            'current_drivers_license_back': _("Update Driver's License (Back)"),
            'current_id_card_front': _("Update National ID (Front)"),
            'current_id_card_back': _("Update National ID (Back)"),
            'current_vehicle_picture': _("Update Vehicle Picture"),
        }
        help_texts = {
             'phone_number': _("Your primary contact number for deliveries."),
             'address': _("Primary area you operate in."),
             'license_number': _("If applicable for your vehicle type."),
             'current_vehicle_registration_document': _("Upload a new copy if your vehicle registration has changed or needs updating."),
             'current_drivers_license_front': _("Upload a new copy of the front of your driver's license if it has been renewed or changed."),
             'current_drivers_license_back': _("Upload a new copy of the back of your driver's license."),
             'current_id_card_front': _("Upload a new copy of the front of your National ID if it has changed."),
             'current_id_card_back': _("Upload a new copy of the back of your National ID."),
             'current_vehicle_picture': _("Upload a new picture of your vehicle if it has changed or the previous one is outdated."),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['profile_picture'].initial = self.user.profile_picture
        self.fields['license_number'].required = False
        # Make new document fields optional
        self.fields['current_vehicle_registration_document'].required = False
        self.fields['current_drivers_license_front'].required = False
        self.fields['current_drivers_license_back'].required = False
        self.fields['current_id_card_front'].required = False
        self.fields['current_id_card_back'].required = False
        self.fields['current_vehicle_picture'].required = False


    def save(self, commit=True):
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', self.user.first_name)
            self.user.last_name = self.cleaned_data.get('last_name', self.user.last_name)
            if 'profile_picture' in self.cleaned_data:
                 self.user.profile_picture = self.cleaned_data['profile_picture']
            elif 'profile_picture' in self.fields and self.fields['profile_picture'].widget.is_initial(self.user.profile_picture) and not self.cleaned_data.get('profile_picture'):
                 self.user.profile_picture = None
            if commit:
                self.user.save()
        rider_profile = super().save(commit=False)
        if commit:
            rider_profile.save()
        return rider_profile
# --- END: Rider Profile Update Form ---


# --- START: Portfolio Item Form ---
class PortfolioItemForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = ['title', 'description', 'image', 'video_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Title for this portfolio piece (optional)')}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': _('Brief description (optional)')}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('e.g., https://www.youtube.com/watch?v=your_video_id')}),
        }

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get("image")
        video_url = cleaned_data.get("video_url")

        if not image and not video_url:
            raise forms.ValidationError(_("Please provide either an image or a video URL for your portfolio item."))
        return cleaned_data
# --- END: Portfolio Item Form ---

# --- START: Rider Payout Request Form ---
class RiderPayoutRequestForm(forms.ModelForm):
    class Meta:
        model = PayoutRequest
        fields = ['amount_requested'] # Only amount is needed from rider for now
        widgets = {
            'amount_requested': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': _('Enter amount to withdraw')}),
        }

    def __init__(self, *args, **kwargs):
        self.max_amount = kwargs.pop('max_amount', None)
        super().__init__(*args, **kwargs)
        if self.max_amount is not None:
            self.fields['amount_requested'].widget.attrs['max'] = str(self.max_amount)
            self.fields['amount_requested'].help_text = _(f"Maximum available: {self.max_amount}")
            self.fields['amount_requested'].validators.append(MaxValueValidator(self.max_amount))
            self.fields['amount_requested'].validators.append(MinValueValidator(Decimal('1.00'))) # Example minimum
# --- END: Rider Payout Request Form ---

# --- START: Vendor Payout Request Form ---
class VendorPayoutRequestForm(forms.ModelForm):
    class Meta:
        model = PayoutRequest
        fields = ['amount_requested', 'payment_method_details'] # Include payment_method_details
        widgets = {
            'amount_requested': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Amount you want to withdraw')}),
            'payment_method_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('E.g., Bank Name, Account Number, Mobile Money Number & Name.')}),
        }

    def __init__(self, *args, **kwargs):
        self.vendor_profile = kwargs.pop('vendor_profile', None) # To potentially use for validation
        super().__init__(*args, **kwargs)

    def clean_amount_requested(self):
        amount = self.cleaned_data.get('amount_requested')
        if amount is not None and amount <= 0:
            raise ValidationError(_("The requested amount must be greater than zero."))
        # Add more validation here if needed, e.g., check against vendor's available balance
        return amount
# --- END: Vendor Payout Request Form ---

# --- START: Service Provider Payout Request Form ---
class ServiceProviderPayoutRequestForm(forms.ModelForm):
    class Meta:
        model = PayoutRequest
        fields = ['amount_requested', 'payment_method_details']
        widgets = {
            'amount_requested': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Amount you want to withdraw')}),
            'payment_method_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('E.g., Mobile Money Number & Registered Name.')}),
        }

    def __init__(self, *args, **kwargs):
        self.service_provider_profile = kwargs.pop('service_provider_profile', None)
        super().__init__(*args, **kwargs)
        self.fields['payment_method_details'].help_text = _("Provide your Mobile Money number and the name registered to it. Payouts are typically via Mobile Money.")

    def clean_amount_requested(self):
        amount = self.cleaned_data.get('amount_requested')
        if amount is not None and amount <= 0:
            raise ValidationError(_("The requested amount must be greater than zero."))
        # TODO: Add validation against provider's available balance
        return amount
# --- END: Vendor Payout Request Form ---
# --- END: Rider Payout Request Form ---
