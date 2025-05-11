# c:\Users\Hp\Desktop\Nexus\authapp\models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _ # For verbose names

# Define your CustomUser model here, inheriting from AbstractUser
class CustomUser(AbstractUser):
    # You MUST define the model specified in settings.AUTH_USER_MODEL

    # Add any extra fields you want your user to have beyond the defaults.
    # Example (optional fields):
    bio = models.TextField(blank=True, null=True, help_text="A short biography.")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name=_("Date of Birth"))
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, verbose_name=_("Profile Picture")) # Added from a previous version

    # --- START: Public Contact Information for Service Providers (and general users) ---
    public_phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Public Phone Number"))
    public_email_contact = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_("Public Contact Email")) # Renamed to avoid clash with user's login email
    website_url = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("Website URL"))
    # Social Media Links
    facebook_url = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("Facebook Profile URL"))
    instagram_url = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("Instagram Profile URL"))
    twitter_url = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("Twitter (X) Profile URL"))
    linkedin_url = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("LinkedIn Profile URL"))
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True,
                                       verbose_name=_("WhatsApp Number"),
                                       help_text=_("Include country code, e.g., +12345678900. This will be visible."))
    # --- END: Public Contact Information ---

    # You don't need to redefine username, email, password, first_name, last_name, etc.
    # They are inherited from AbstractUser.

    # Add a __str__ method for better representation in the admin
    def __str__(self):
        return self.username

    # You can add custom methods here if needed
    # def get_full_name(self):
    #     # Example override or custom method
    #     return f"{self.first_name} {self.last_name}".strip()
