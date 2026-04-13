from django.contrib import admin
from .models import Stadium, Match, Seat, Booking, UserProfile

@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'total_seats']

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['home_team', 'away_team', 'match_date', 'stadium', 'price', 'is_active']
    list_filter = ['is_active', 'stadium', 'match_date']
    search_fields = ['home_team', 'away_team']

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['stadium', 'row_number', 'seat_number', 'section']
    list_filter = ['stadium', 'section']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_code', 'customer_name', 'match', 'total_price', 'status', 'booking_date']
    list_filter = ['status', 'booking_date']
    search_fields = ['booking_code', 'customer_name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'points', 'total_bookings', 'total_spent']
    list_filter = ['level']
    search_fields = ['user__username']