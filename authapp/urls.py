from django.urls import path
from authapp import views

app_name = 'authapp'  # <<< Add this line



urlpatterns = [
    
    path('signup/', views.register_view, name='signup'),
    path('signin/', views.signin, name='signin'), # <<< Add this line
    path('signout/', views.signout, name='signout'), # <<< Add this line
   
]
