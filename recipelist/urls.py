from django.urls import path
from . import views

app_name = 'recipelist'
urlpatterns = [
    path("", views.index, name='index'),
    path('search/', views.search, name='search'),
    path('favorites/', views.favorites, name='favorites'),
    path('favorites/add/', views.add_favorite, name='add_favorite'),
    path('favorites/<int:pk>/remove/', views.remove_favorite, name='remove_favorite'),
    path('grocery_list/', views.grocery_list, name='grocery_list'),
    path('send_to_origo/', views.send_to_origo, name='send_to_origo'),
]
