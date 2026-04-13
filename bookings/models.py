from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import secrets

# Добавь эту модель в конец файла (перед class Stadium)
class UserProfile(models.Model):
    USER_LEVELS = [
        ('bronze', 'Бронзовый болельщик'),
        ('silver', 'Серебряный болельщик'),
        ('gold', 'Золотой болельщик'),
        ('platinum', 'Платиновый болельщик'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    points = models.IntegerField('Баллы', default=0)
    level = models.CharField('Уровень', max_length=20, choices=USER_LEVELS, default='bronze')
    total_bookings = models.IntegerField('Всего бронирований', default=0)
    total_spent = models.DecimalField('Потрачено всего', max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_level_display()} ({self.points} баллов)"
    
    def update_level(self):
        if self.points >= 5000:
            self.level = 'platinum'
        elif self.points >= 2000:
            self.level = 'gold'
        elif self.points >= 500:
            self.level = 'silver'
        else:
            self.level = 'bronze'
        self.save()
    
    def add_points(self, points):
        self.points += points
        self.update_level()
        self.save()

# Сигналы для автоматического создания профиля
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# Остальные модели (Stadium, Match, Seat, Booking) остаются без изменений
class Stadium(models.Model):
    name = models.CharField('Название', max_length=200)
    address = models.TextField('Адрес')
    total_seats = models.IntegerField('Всего мест')
    rows = models.IntegerField('Ряды', default=10)
    seats_per_row = models.IntegerField('Мест в ряду', default=20)

    def __str__(self):
        return self.name

class Match(models.Model):
    home_team = models.CharField('Хозяева', max_length=100)
    away_team = models.CharField('Гости', max_length=100)
    match_date = models.DateTimeField('Дата и время')
    stadium = models.ForeignKey(Stadium, on_delete=models.CASCADE)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, default=500)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"

    @property
    def available_seats_count(self):
        booked = Booking.objects.filter(match=self, status='confirmed').count()
        return self.stadium.total_seats - booked

class Seat(models.Model):
    stadium = models.ForeignKey(Stadium, on_delete=models.CASCADE)
    row_number = models.IntegerField('Номер ряда')
    seat_number = models.IntegerField('Номер места')
    section = models.CharField('Сектор', max_length=50, default='Центральный')

    class Meta:
        unique_together = ['stadium', 'row_number', 'seat_number']

    def __str__(self):
        return f"Ряд {self.row_number} Место {self.seat_number}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
    ]

    booking_code = models.CharField(max_length=10, unique=True, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    seats = models.ManyToManyField(Seat)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField('Имя', max_length=200)
    customer_phone = models.CharField('Телефон', max_length=20)
    customer_email = models.EmailField('Email', blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    booking_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.booking_code:
            self.booking_code = secrets.token_hex(4).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_code} - {self.customer_name}"