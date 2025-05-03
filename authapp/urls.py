from django.urls import path
from authapp import views

app_name = 'authapp'

urlpatterns = [
    
    path('signup/', views.register_view, name='signup'),
   
]

