# c:\Users\Hp\Desktop\Nexus\authapp\forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser # Assuming CustomUser is in authapp.models
from django.utils.translation import gettext_lazy as _


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email',] # Only username and email are directly handled by UserCreationForm's Meta

    def save(self, request):
        """
        Overrides the default save method to be compatible with allauth's
        expectation of a `save(self, request)` signature for custom signup forms.
        It calls the parent UserCreationForm's save method.
        """
        # UserCreationForm.save() handles user creation, password setting, and saving.
        user = super().save(commit=True)
        return user

    def signup(self, request, user):
        """
        Required by allauth if ACCOUNT_SIGNUP_FORM_CLASS is used.
        The `user` object is already created and saved by the `save` method above
        (which calls UserCreationForm's save).
        This method is a hook for any additional allauth-specific signup steps.
        """
        # The user is already saved by UserCreationForm's save method.
        # You can add additional logic here if needed, e.g., populating profile fields.
        return user


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'bio', 'profile_picture', 'date_of_birth',
            # New public contact and social media fields
            'public_phone_number', 'public_email_contact', 'website_url',
            'facebook_url', 'instagram_url', 'twitter_url', 'linkedin_url', 'whatsapp_number'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            # Widgets for new fields
            'public_phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g., +1234567890')}),
            'public_email_contact': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('public_contact@example.com')}),
            'website_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://yourwebsite.com')}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://facebook.com/yourpage')}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://instagram.com/yourprofile')}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://twitter.com/yourhandle')}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://linkedin.com/in/yourprofile')}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('+12345678900')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can add custom initialization logic here if needed
        # For example, making certain fields not required if they are optional
        self.fields['bio'].required = False
        self.fields['profile_picture'].required = False
        self.fields['date_of_birth'].required = False
        self.fields['public_phone_number'].required = False
        self.fields['public_email_contact'].required = False
        self.fields['website_url'].required = False
        self.fields['facebook_url'].required = False
        self.fields['instagram_url'].required = False
        self.fields['twitter_url'].required = False
        self.fields['linkedin_url'].required = False
        self.fields['whatsapp_number'].required = False
