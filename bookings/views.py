from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Match, Booking, Seat
from .forms import RegisterForm

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

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Регистрация успешна.')
            return redirect('index')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = RegisterForm()
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

@login_required
def match_detail(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    booked_seats = Booking.objects.filter(
        match=match,
        status='confirmed'
    ).values_list('seats__id', flat=True)

    stadium_map = []
    for row in range(1, match.stadium.rows + 1):
        row_seats = []
        for seat_num in range(1, match.stadium.seats_per_row + 1):
            seat = Seat.objects.filter(
                stadium=match.stadium,
                row_number=row,
                seat_number=seat_num
            ).first()
            if seat:
                row_seats.append({
                    'id': seat.id,
                    'row': row,
                    'number': seat_num,
                    'is_booked': seat.id in booked_seats,
                    'section': seat.section
                })
        stadium_map.append(row_seats)

    return render(request, 'bookings/match_detail.html', {
        'match': match,
        'stadium_map': stadium_map,
        'available_seats': match.available_seats_count,
    })

@login_required
def create_booking(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        seat_ids = request.POST.getlist('selected_seats')

        if not name or not phone or not seat_ids:
            messages.error(request, 'Заполните все поля')
            return redirect('match_detail', match_id=match_id)

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
    
    return redirect('match_detail', match_id=match_id)

@login_required
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