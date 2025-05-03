# core/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _ # For labels/help text
# Import models needed for forms
from .models import VendorReview, ProductReview, Vendor, Promotion, AdCampaign, Product, Category # <<< Import new models
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
        fields = ['rating', 'review', 'video'] # <<< Add 'video' field here
        widgets = {
            # Use radio buttons for rating, apply Bootstrap classes
            'rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            # Use a textarea for the review text
            'review': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Share your thoughts on this product...'}),
            # Add widget for video if needed (default FileInput is often fine)
            'video': forms.ClearableFileInput(attrs={'class': 'form-control'}), # Example using ClearableFileInput
        }
        labels = {
            'rating': 'Your Rating*', # Mark required fields
            'review': 'Your Review',
            'video': 'Upload Video (Optional)', # Add label for video
        }
        help_texts = { # Optional: Add help text if needed
            'video': 'Upload a short video showing the product (MP4, WebM recommended).'
        }
# --- End ProductReviewForm ---

# --- VendorRegistrationForm ---
class VendorRegistrationForm(forms.ModelForm):
    """
    Form for users to apply to become vendors. Simplified for initial registration.
    Verification details will be collected later.
    """
    # Removed registration_type, agree_to_terms, and verification doc fields
    # These will be handled later, likely in a vendor dashboard/profile update form.

    class Meta:
        model = Vendor
        # Select fields needed for initial registration
        # Exclude fields like 'user', 'is_approved', 'is_verified', 'slug' which will be set later
        # Keep only essential fields for initial setup
        fields = ['name', 'contact_email', 'phone_number', 'description', 'logo']

        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Briefly describe your business and the products you sell...'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'placeholder': 'Your Business Name'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'Business Contact Email'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Business Phone Number'}),
            # Removed widgets for verification fields
        }

    # Removed __init__ and clean methods related to conditional fields

# --- End VendorRegistrationForm ---

# --- VendorVerificationForm ---
class VendorVerificationForm(forms.ModelForm):
    # --- Choices ---
    """
    Form for vendors to submit their verification documents (Business Reg or National ID).
    """
    REGISTRATION_TYPE_CHOICES = (
        ('business', 'I have a registered business'),
        ('individual', 'I am registering as an individual (using National ID)'),
    )
    GHANA_ID_CHOICES = (
        ('', '---------'), # Add a blank option
        ('national_id', 'National ID'), # Changed from Ghana Card
        ('passport', 'Passport'),
        ('drivers_license', 'Driver\'s License'),
    )
    AFRICAN_COUNTRIES = ( # Example list, expand as needed
        ('', '---------'),
        ('GH', 'Ghana'),
        ('NG', 'Nigeria'),
        ('KE', 'Kenya'),
        ('ZA', 'South Africa'),
        ('EG', 'Egypt'),
        ('MA', 'Morocco'),
        ('ET', 'Ethiopia'),
        ('TZ', 'Tanzania'),
        ('UG', 'Uganda'),
        ('DZ', 'Algeria'),
        ('SD', 'Sudan'),
        ('AO', 'Angola'),
        ('MZ', 'Mozambique'),
        ('MG', 'Madagascar'),
        ('CM', 'Cameroon'),
        ('CI', 'Côte d\'Ivoire'),
        ('NE', 'Niger'),
        ('BF', 'Burkina Faso'),
        ('ML', 'Mali'),
        ('MW', 'Malawi'),
        ('ZM', 'Zambia'),
        ('SN', 'Senegal'),
        ('TD', 'Chad'),
        ('SO', 'Somalia'),
        ('ZW', 'Zimbabwe'),
        ('GN', 'Guinea'),
        ('RW', 'Rwanda'),
        # Add more countries...
    )

    registration_type = forms.ChoiceField(
        choices=REGISTRATION_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input verification-radio'}), # Added class for JS
        label="Verification Method",
        required=True,
    )
    # Use the existing model field, but override widget and choices
    location_country = forms.ChoiceField(
        choices=AFRICAN_COUNTRIES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Country of Operation",
        required=False, # Required conditionally in clean()
    )
    # Override national_id_type to use choices
    national_id_type = forms.ChoiceField(
        choices=GHANA_ID_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Type of National ID",
        required=False, # Required conditionally in clean()
    )
    agree_to_terms = forms.BooleanField(
        required=True,
        label=_("I confirm the provided information is accurate and agree to the Vendor Terms and Conditions"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Vendor
        # Only include fields relevant to verification from the model
        fields = [
            'business_registration_doc',
            'tax_id_number', # Add TIN
            'other_business_doc', # Add other doc
            'location_country', # Add country field
            'national_id_type',
            'national_id_number',
            'national_id_doc',
        ]
        labels = { # Add labels for clarity
            'business_registration_doc': _("Business Registration Document"),
            'location_country': _("Country of Operation"), # Label for country
            'tax_id_number': _("Tax Identification Number (TIN)"), # Label for TIN
            'other_business_doc': _("Other Supporting Document (Optional)"), # Label for other doc
            # 'national_id_type' label is set on the field definition above
            'national_id_number': _("National ID Number"),
            'national_id_doc': _("National ID Document"),
        }
        widgets = {
            # Apply Bootstrap classes using widgets
            'business_registration_doc': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'tax_id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your Business TIN'}), # Widget for TIN
            'other_business_doc': forms.ClearableFileInput(attrs={'class': 'form-control'}), # Widget for other doc
            # 'location_country' and 'national_id_type' widgets set on field definitions above
            'national_id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ID Number'}),
            'national_id_doc': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        # Ensure fields are not required by default in Meta, clean method handles it
        extra_kwargs = { field: {'required': False} for field in fields }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value for registration_type if instance has docs
        instance = kwargs.get('instance')
        if instance:
            if instance.business_registration_doc or instance.tax_id_number:
                self.fields['registration_type'].initial = 'business'
            elif instance.national_id_doc or instance.national_id_number:
                self.fields['registration_type'].initial = 'individual'

    def clean(self):
        cleaned_data = super().clean()
        registration_type = cleaned_data.get('registration_type') # Get type from non-model field

        if registration_type == 'business':
            # Business registration doc is required
            business_doc = cleaned_data.get('business_registration_doc')
            tax_id = cleaned_data.get('tax_id_number')
            # Check if a file is being uploaded OR if one already exists and isn't being cleared
            if not business_doc and not (self.instance and self.instance.business_registration_doc and not self.fields['business_registration_doc'].widget.is_initial(business_doc)):
                 self.add_error('business_registration_doc', 'This field is required when registering as a business.')
            # Check TIN
            if not tax_id:
                self.add_error('tax_id_number', 'Tax ID Number is required when registering as a business.')
            # Clear any potentially submitted individual fields
            cleaned_data['location_country'] = '' # Clear country if business
            cleaned_data['national_id_type'] = '' # Set to blank choice value
            cleaned_data['national_id_number'] = None
            cleaned_data['national_id_doc'] = None
        elif registration_type == 'individual':
            # National ID fields are required
            id_type = cleaned_data.get('national_id_type')
            id_number = cleaned_data.get('national_id_number')
            id_doc = cleaned_data.get('national_id_doc')
            location_country = cleaned_data.get('location_country') # Get country here

            has_existing_id_doc = self.instance and self.instance.national_id_doc and not self.fields['national_id_doc'].widget.is_initial(id_doc)

            # Validate country (only required for individual)
            if not location_country: self.add_error('location_country', 'Please select your country of operation.')
            # Validate ID fields
            if not id_type: self.add_error('national_id_type', 'This field is required for individual registration.')
            if not id_number: self.add_error('national_id_number', 'This field is required for individual registration.')
            if not id_doc and not has_existing_id_doc:
                self.add_error('national_id_doc', 'This field is required for individual registration.')

            # Clear any potentially submitted business field
            cleaned_data['business_registration_doc'] = None
            cleaned_data['tax_id_number'] = None
            cleaned_data['other_business_doc'] = None
        else:
            # This case should ideally not be reached if registration_type field is required=True
             self.add_error('registration_type', 'Please select a verification method.')

        # Check terms agreement
        if not cleaned_data.get('agree_to_terms'):
            self.add_error('agree_to_terms', 'You must agree to the terms and conditions.')

        return cleaned_data

# --- End VendorVerificationForm ---

# --- VendorProfileUpdateForm ---
class VendorProfileUpdateForm(forms.ModelForm):
    """
    Form for vendors to update their public profile information.
    """
    class Meta:
        model = Vendor
        # Fields vendors can edit on their profile
        fields = [
            'name', 'description', 'contact_email', 'phone_number',
            'logo', 'location_city', 'location_country',
            'shipping_policy', 'return_policy'
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
        }

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
    Form for vendors to update their payment information (e.g., Mobile Money).
    """
    # Example choices, adjust as needed
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
    # Use widgets for date/time fields if needed (e.g., SplitDateTimeWidget)
    start_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    end_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))

    # Use ModelMultipleChoiceField for ManyToMany relations
    applicable_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple, # Or forms.SelectMultiple(attrs={'class': 'form-select'})
        required=False,
        help_text=_("Select categories if scope is 'Specific Category'.")
    )
    applicable_products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.none(), # Queryset will be set in the view based on vendor
        widget=forms.CheckboxSelectMultiple, # Or forms.SelectMultiple(attrs={'class': 'form-select'})
        required=False,
        help_text=_("Select products if scope is 'Specific Product(s)'.")
    )

    class Meta:
        model = Promotion
        # Exclude fields set automatically or not directly editable by vendor
        exclude = ['vendor', 'current_uses', 'created_at', 'applicable_vendor'] # Exclude applicable_vendor if scope='vendor' is handled differently
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
        # Pop vendor from kwargs before passing to super
        vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)
        # Limit product choices to the specific vendor's products
        if vendor:
            self.fields['applicable_products'].queryset = Product.objects.filter(vendor=vendor, is_active=True)
        # TODO: Add logic to show/hide scope fields based on 'scope' selection using JS

# --- End PromotionForm ---

# --- AdCampaignForm ---
class AdCampaignForm(forms.ModelForm):
    """
    Form for vendors to create or update ad campaigns.
    """
    start_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    end_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    promoted_product = forms.ModelChoiceField(
        queryset=Product.objects.none(), # Queryset set in view
        required=False, # Allow promoting the whole store
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text=_("Select a product to promote, or leave blank to promote your store.")
    )

    class Meta:
        model = AdCampaign
        exclude = ['vendor', 'created_at'] # Vendor set automatically
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
    # Ensure category choices are active
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Product
        # Fields the vendor can manage
        fields = [
            'category', 'name', 'description', 'price',
            'stock', 'is_active', 'is_featured'
            # Exclude 'vendor' (set automatically), 'slug' (auto-generated)
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
# --- End VendorProductForm ---
