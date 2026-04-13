from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Sum
from .models import Match, Booking, Seat, UserProfile, Stadium
from .forms import CustomRegisterForm, UserProfileForm
from decimal import Decimal

# ==================== ГЛАВНАЯ СТРАНИЦА С ПОИСКОМ ====================
def index(request):
    matches = Match.objects.filter(
        match_date__gte=timezone.now(),
        is_active=True
    ).order_by('match_date')
    
    # Поиск по командам
    search_query = request.GET.get('search', '')
    if search_query:
        matches = matches.filter(
            Q(home_team__icontains=search_query) |
            Q(away_team__icontains=search_query)
        )
    
    # Фильтр по стадиону
    stadium_filter = request.GET.get('stadium', '')
    if stadium_filter:
        matches = matches.filter(stadium__id=stadium_filter)
    
    # Фильтр по дате
    date_filter = request.GET.get('date', '')
    if date_filter:
        matches = matches.filter(match_date__date=date_filter)
    
    past_matches = Match.objects.filter(
        match_date__lt=timezone.now()
    ).order_by('-match_date')[:5]
    
    # Список стадионов для фильтра
    stadiums = Stadium.objects.all()
    
    return render(request, 'bookings/index.html', {
        'upcoming_matches': matches,
        'past_matches': past_matches,
        'stadiums': stadiums,
        'search_query': search_query,
        'stadium_filter': stadium_filter,
        'date_filter': date_filter,
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


# ==================== ЛИЧНЫЙ КАБИНЕТ ====================
@login_required
def profile_view(request):
    profile = request.user.profile
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    
    total_bookings = bookings.count()
    total_spent = bookings.aggregate(total=Sum('total_price'))['total'] or 0
    active_bookings = bookings.filter(status='confirmed', match__match_date__gte=timezone.now()).count()
    
    next_level_points = 0
    next_level_name = ''
    if profile.level == 'bronze':
        next_level_points = 500 - profile.points
        next_level_name = 'Серебряный болельщик'
    elif profile.level == 'silver':
        next_level_points = 2000 - profile.points
        next_level_name = 'Золотой болельщик'
    elif profile.level == 'gold':
        next_level_points = 5000 - profile.points
        next_level_name = 'Платиновый болельщик'
    
    context = {
        'profile': profile,
        'bookings': bookings,
        'total_bookings': total_bookings,
        'total_spent': total_spent,
        'active_bookings': active_bookings,
        'next_level_points': next_level_points,
        'next_level_name': next_level_name,
    }
    return render(request, 'bookings/profile.html', context)


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('profile')
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'bookings/profile_edit.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменён!')
            return redirect('profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'bookings/change_password.html', {'form': form})


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
        
        # Исправлено: получаем строку с ID и разбиваем на список
        selected_seats_raw = request.POST.get('selected_seats', '')
        if selected_seats_raw:
            seat_ids = selected_seats_raw.split(',')
        else:
            seat_ids = []
        
        if not name or not phone or not seat_ids:
            messages.error(request, 'Заполните все поля и выберите хотя бы одно место')
            return redirect('select_seats', match_id=match_id, row_number=row_number)
        
        # Получаем список занятых мест
        booked_seats = Booking.objects.filter(
            match=match,
            status='confirmed'
        ).values_list('seats__id', flat=True)
        
        # Проверяем каждое место
        for seat_id in seat_ids:
            if int(seat_id) in booked_seats:
                messages.error(request, 'Некоторые выбранные места уже заняты')
                return redirect('select_seats', match_id=match_id, row_number=row_number)
        
        from decimal import Decimal
        total_price = len(seat_ids) * Decimal(str(match.price))
        
        booking = Booking.objects.create(
            match=match,
            user=request.user,
            customer_name=name,
            customer_phone=phone,
            customer_email=email,
            total_price=total_price,
            status='confirmed'
        )
        booking.seats.set(Seat.objects.filter(id__in=seat_ids))
        
        points_earned = int(total_price / 10)
        profile = request.user.profile
        profile.add_points(points_earned)
        profile.total_bookings += 1
        profile.total_spent += Decimal(str(total_price))
        profile.save()
        
        messages.success(request, f'Бронирование создано! Начислено {points_earned} баллов. Код: {booking.booking_code}')
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