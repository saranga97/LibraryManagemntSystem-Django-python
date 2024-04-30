from django.urls import path,include
from . import views
from django.contrib.auth.models import User

urlpatterns = [
    path('', views.user_login, name='user_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('user/register/', views.user_register, name='user_register'),
    path('user/login/', views.user_login, name='user_login'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('catalog/', views.catalog, name='catalog'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('edit_book/<int:book_id>/', views.edit_book, name='edit_book'),
    path('remove_book/<int:book_id>/', views.remove_book, name='remove_book'),
    path('borrow/', views.borrow_book, name='borrow_book'),
    path('my_books/', views.my_books, name='my_books'),
    path('accounts/', include('django.contrib.auth.urls')),  # Include authentication URLs
]
