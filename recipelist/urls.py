from django.urls import path
from . import views

app_name = 'recipelist'
urlpatterns = [
    path("", views.index, name='index'),
    path('search/', views.search, name='search'),
    path('grocery_list/', views.grocery_list, name='grocery_list'),
    path('login_heb/', views.login_heb, name='login_heb'),
]
