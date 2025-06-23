# C:\Users\Hp\Desktop\Nexus\authapp\views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import UserRegisterForm # Import your registration form
from django.utils.translation import gettext_lazy as _

def signin(request): # Renamed from signin_view to match import
    if request.user.is_authenticated:
        return redirect('core:home') # Redirect if already logged in

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username') # Or email if using email for login
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, _("You are now logged in as {username}.").format(username=user.get_username()))
                # Redirect to a success page, e.g., the previous page or home
                next_url = request.GET.get('next')
                return redirect(next_url or 'core:home')
            else:
                messages.error(request, _("Invalid username or password."))
        else:
            # Form is not valid, errors will be displayed by the template
            messages.error(request, _("Invalid username or password. Please check your input."))
    else:
        form = AuthenticationForm()
    return render(request, 'authapp/signin.html', {'form': form, 'page_title': _('Sign In')})

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST) # Use your custom form
        if form.is_valid():
            # Your UserRegisterForm has a save method that takes 'request'
            # due to allauth compatibility.
            user = form.save(request=request) # Pass the request object
            # login(request, user) # Allauth might handle login automatically if configured, or you can do it explicitly
            messages.success(request, _("Registration successful. Please check your email to verify your account if required."))
            # Redirect to a page indicating to check email, or home if verification is optional/none
            # For now, let's redirect to signin, as allauth often requires email verification before login.
            return redirect("authapp:signin") # Or 'core:home' if auto-login is desired and no verification
        else: # Form is not valid
            messages.error(request, _("Unsuccessful registration. Please correct the errors below."))
    else: # GET request
        form = UserRegisterForm()
    # Pass the form with the key 'form'
    return render(request=request, template_name="authapp/signup.html", context={"form": form, "page_title": _("Sign Up")})

def signout(request): # Renamed from signout_view to match import
    logout(request)
    messages.info(request, _("You have successfully logged out."))
    return redirect("core:home") # Redirect to home page or signin page
