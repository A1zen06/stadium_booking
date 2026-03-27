from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('match/<int:match_id>/', views.match_detail, name='match_detail'),
    path('match/<int:match_id>/book/', views.create_booking, name='create_booking'),
    path('booking/<str:booking_code>/', views.booking_success, name='booking_success'),
    path('check/', views.check_booking, name='check_booking'),
    path('my/', views.my_bookings, name='my_bookings'),
    path('cancel/<str:booking_code>/', views.cancel_booking, name='cancel_booking'),
]