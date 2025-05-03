# authapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages # <<< Import messages
from django.urls import reverse
from .forms import UserRegisterForm # Import the registration form

def register_view(request):
    """Handles user registration."""
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('core:home') # Redirect logged-in users away

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log the user in immediately after registration
            messages.success(request, f"Registration successful! Welcome, {user.username}!")
            return redirect('core:home') # Redirect to home page after successful registration
        else:
            # Form is invalid, add error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            # No need to explicitly pass form errors to context, Django handles it
    else:
        form = UserRegisterForm()

    context = {'form': form}
    # Make sure you have a template at 'authapp/register.html'
    return render(request, 'authapp/register.html', context)
