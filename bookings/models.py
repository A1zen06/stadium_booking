from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import secrets

class Stadium(models.Model):
    name = models.CharField('Название', max_length=200)
    address = models.TextField('Адрес')
    total_seats = models.IntegerField('Всего мест')
    rows = models.IntegerField('Ряды', default=10)
    seats_per_row = models.IntegerField('Мест в ряду', default=20)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Стадион'
        verbose_name_plural = 'Стадионы'

class Match(models.Model):
    home_team = models.CharField('Хозяева', max_length=100)
    away_team = models.CharField('Гости', max_length=100)
    match_date = models.DateTimeField('Дата и время')
    stadium = models.ForeignKey(Stadium, on_delete=models.CASCADE, verbose_name='Стадион')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, default=500)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} - {self.match_date.strftime('%d.%m.%Y %H:%M')}"

    @property
    def available_seats_count(self):
        booked = Booking.objects.filter(match=self, status='confirmed').count()
        return self.stadium.total_seats - booked

    class Meta:
        verbose_name = 'Матч'
        verbose_name_plural = 'Матчи'
        ordering = ['match_date']

class Seat(models.Model):
    stadium = models.ForeignKey(Stadium, on_delete=models.CASCADE, verbose_name='Стадион')
    row_number = models.IntegerField('Номер ряда')
    seat_number = models.IntegerField('Номер места')
    section = models.CharField('Сектор', max_length=50, default='Центральный')

    class Meta:
        unique_together = ['stadium', 'row_number', 'seat_number']
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def __str__(self):
        return f"Ряд {self.row_number} Место {self.seat_number}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
    ]

    booking_code = models.CharField('Код бронирования', max_length=10, unique=True, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, verbose_name='Матч')
    seats = models.ManyToManyField(Seat, verbose_name='Места')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Пользователь')  # <- ЭТУ СТРОКУ ДОБАВЬ
    customer_name = models.CharField('Имя', max_length=200)
    customer_phone = models.CharField('Телефон', max_length=20)
    customer_email = models.EmailField('Email', blank=True)
    total_price = models.DecimalField('Общая стоимость', max_digits=10, decimal_places=2)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='confirmed')
    booking_date = models.DateTimeField('Дата бронирования', auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.booking_code:
            self.booking_code = secrets.token_hex(4).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_code} - {self.customer_name}"

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-booking_date']