
#
from django.urls import path

import mplace.views
from django.contrib.auth import views as auth_views
from . import views

app_name = 'mplace'
urlpatterns = [
    path('', mplace.views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    path('', mplace.views.home, name='home'),
    path('market/', mplace.views.market, name='market'),
    path('contact/', mplace.views.contact, name='contact'),
    path('market/<slug:slug>/', mplace.views.detail_market, name='detail_market'),
]
