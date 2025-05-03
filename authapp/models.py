from django.db import models
from django.contrib.auth.models import AbstractUser

# Remove the incorrect/misplaced form imports below:
# from django import UserCreationForm  # REMOVE THIS LINE
# from django.contrib.auth.forms import UserChangeForm # REMOVE THIS LINE

# Define your CustomUser model here, inheriting from AbstractUser
class CustomUser(AbstractUser):
    # You MUST define the model specified in settings.AUTH_USER_MODEL

    # Add any extra fields you want your user to have beyond the defaults.
    # Example (optional fields):
    bio = models.TextField(blank=True, null=True, help_text="A short biography.")
    date_of_birth = models.DateField(blank=True, null=True)

    # You don't need to redefine username, email, password, first_name, last_name, etc.
    # They are inherited from AbstractUser.

    # Add a __str__ method for better representation in the admin
    def __str__(self):
        return self.username

    # You can add custom methods here if needed
    # def get_full_name(self):
    #     # Example override or custom method
    #     return f"{self.first_name} {self.last_name}".strip()




    
  