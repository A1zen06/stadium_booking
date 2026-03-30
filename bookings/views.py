from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Match, Booking, Seat
from .forms import CustomRegisterForm


# ==================== ГЛАВНАЯ СТРАНИЦА ====================
def index(request):
    upcoming_matches = Match.objects.filter(
        match_date__gte=timezone.now(),
        is_active=True
    ).order_by('match_date')
    
    past_matches = Match.objects.filter(
        match_date__lt=timezone.now()
    ).order_by('-match_date')[:5]
    
    return render(request, 'bookings/index.html', {
        'upcoming_matches': upcoming_matches,
        'past_matches': past_matches,
    })


# ==================== АУТЕНТИФИКАЦИЯ ====================
def register(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Регистрация успешна.')
            return redirect('index')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CustomRegisterForm()
    return render(request, 'bookings/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}!')
            return redirect('index')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'bookings/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('index')


# ==================== ВЫБОР РЯДА И МЕСТ ====================
@login_required
def select_row(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    rows = range(1, match.stadium.rows + 1)
    
    booked_seats = Booking.objects.filter(
        match=match,
        status='confirmed'
    ).values_list('seats__id', flat=True)
    
    rows_data = []
    for row in rows:
        seats_in_row = Seat.objects.filter(
            stadium=match.stadium,
            row_number=row
        )
        total_in_row = seats_in_row.count()
        booked_in_row = seats_in_row.filter(id__in=booked_seats).count()
        free_in_row = total_in_row - booked_in_row
        
        rows_data.append({
            'number': row,
            'total': total_in_row,
            'free': free_in_row,
            'booked': booked_in_row
        })
    
    return render(request, 'bookings/select_row.html', {
        'match': match,
        'rows': rows_data,
    })


@login_required
def select_seats(request, match_id, row_number):
    match = get_object_or_404(Match, id=match_id)
    
    if row_number < 1 or row_number > match.stadium.rows:
        messages.error(request, 'Такого ряда не существует')
        return redirect('select_row', match_id=match_id)
    
    booked_seats = Booking.objects.filter(
        match=match,
        status='confirmed'
    ).values_list('seats__id', flat=True)
    
    seats = Seat.objects.filter(
        stadium=match.stadium,
        row_number=row_number
    ).order_by('seat_number')
    
    seats_data = []
    for seat in seats:
        seats_data.append({
            'id': seat.id,
            'number': seat.seat_number,
            'is_booked': seat.id in booked_seats,
        })
    
    return render(request, 'bookings/select_seats.html', {
        'match': match,
        'row_number': row_number,
        'seats': seats_data,
        'total_seats': len(seats_data),
        'price': match.price,
    })


@login_required
def create_booking(request, match_id, row_number):
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        seat_ids = request.POST.getlist('selected_seats')
        
        if not name or not phone or not seat_ids:
            messages.error(request, 'Заполните все поля и выберите хотя бы одно место')
            return redirect('select_seats', match_id=match_id, row_number=row_number)
        
        booked_seats = Booking.objects.filter(
            match=match,
            status='confirmed'
        ).values_list('seats__id', flat=True)
        
        for seat_id in seat_ids:
            if int(seat_id) in booked_seats:
                messages.error(request, 'Некоторые выбранные места уже заняты')
                return redirect('select_seats', match_id=match_id, row_number=row_number)
        
        booking = Booking.objects.create(
            match=match,
            user=request.user,
            customer_name=name,
            customer_phone=phone,
            customer_email=email,
            total_price=len(seat_ids) * float(match.price),
            status='confirmed'
        )
        booking.seats.set(Seat.objects.filter(id__in=seat_ids))
        
        messages.success(request, f'Бронирование создано! Код: {booking.booking_code}')
        return redirect('booking_success', booking_code=booking.booking_code)
    
    return redirect('select_seats', match_id=match_id, row_number=row_number)


# ==================== БРОНИРОВАНИЯ ====================
def booking_success(request, booking_code):
    booking = get_object_or_404(Booking, booking_code=booking_code)
    return render(request, 'bookings/booking_success.html', {
        'booking': booking,
        'seats': booking.seats.all(),
        'match': booking.match,
    })


def check_booking(request):
    if request.method == 'POST':
        code = request.POST.get('booking_code')
        try:
            booking = Booking.objects.get(booking_code=code)
            return redirect('booking_success', booking_code=code)
        except Booking.DoesNotExist:
            messages.error(request, 'Код бронирования не найден')
    return render(request, 'bookings/check_booking.html')


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def cancel_booking(request, booking_code):
    booking = get_object_or_404(Booking, booking_code=booking_code, user=request.user)
    
    if request.method == 'POST':
        if booking.match.match_date > timezone.now():
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Бронирование отменено')
        else:
            messages.error(request, 'Нельзя отменить бронирование на прошедший матч')
        return redirect('my_bookings')
    
    return render(request, 'bookings/cancel_booking.html', {'booking': booking})