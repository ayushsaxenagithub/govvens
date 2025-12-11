from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Event, Booking
from user.models import User, NotificationSubscription, UserSession, UserActivity
from django.db.models import Count, Avg, Max, Min, Sum
from django.utils.dateparse import parse_date
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime

# Page 1: Landing Page
def landing_page(request):
    """Landing page with real event data"""
    # Fetch real upcoming events from database
    upcoming_events = Event.objects.filter(is_active=True).order_by('date', 'time')[:3]
    
    featured_events = []
    for event in upcoming_events:
        featured_events.append({
            'id': event.id,
            'name': event.name,
            'date': event.date.strftime('%d %B %Y'),
            'time': event.time.strftime('%I:%M %p'),
            'stadium': event.stadium,
            'ticket_price': f'₹{int(event.ticket_price)}',
            'available_seats': event.available_seats
        })
    
    # If no events in DB, show message instead of dummy data
    return render(request, 'website/landing.html', {
        'page_title': 'GOVVENS - Crowd-Safe Ticketing',
        'featured_events': featured_events,
        'has_events': len(featured_events) > 0
    })

# Page 4: Events List
def events_list(request):
    """Events list page"""
    events = Event.objects.filter(is_active=True).order_by('date', 'time')
    # If no events in DB, use mock data
    if not events.exists():
        events_data = [
            {
                'id': 1,
                'name': 'India vs Australia',
                'date': '2025-11-05',
                'time': '18:00',
                'stadium': 'Chinnaswamy Stadium',
                'ticket_price': '₹2500',
                'available_seats': '1200'
            },
            {
                'id': 2,
                'name': 'IPL Final',
                'date': '2025-11-10',
                'time': '19:00',
                'stadium': 'Chinnaswamy Stadium',
                'ticket_price': '₹5000',
                'available_seats': '800'
            },
            {
                'id': 3,
                'name': 'T20 World Cup Match',
                'date': '2025-11-15',
                'time': '17:30',
                'stadium': 'Chinnaswamy Stadium',
                'ticket_price': '₹3500',
                'available_seats': '1500'
            },
            {
                'id': 4,
                'name': 'Asia Cup Semi-Final',
                'date': '2025-11-20',
                'time': '16:00',
                'stadium': 'Chinnaswamy Stadium',
                'ticket_price': '₹2000',
                'available_seats': '2000'
            },
            {
                'id': 5,
                'name': 'World Test Championship',
                'date': '2025-11-25',
                'time': '10:00',
                'stadium': 'Chinnaswamy Stadium',
                'ticket_price': '₹3000',
                'available_seats': '1000'
            }
        ]
    else:
        events_data = [{
            'id': e.id,
            'name': e.name,
            'date': e.date.strftime('%Y-%m-%d'),
            'time': e.time.strftime('%H:%M'),
            'stadium': e.stadium,
            'ticket_price': f'₹{e.ticket_price}',
            'available_seats': str(e.available_seats)
        } for e in events]
    
    return render(request, 'website/events_list.html', {
        'page_title': 'All Upcoming Matches',
        'events': events_data
    })

# Page 5: Event Details
def event_detail(request, event_id):
    """Event details page"""
    try:
        event = Event.objects.get(id=event_id, is_active=True)
        event_data = {
            'id': event.id,
            'name': event.name,
            'date': event.date.strftime('%Y-%m-%d'),
            'time': event.time.strftime('%H:%M'),
            'stadium': event.stadium,
            'ticket_price': f'₹{event.ticket_price}',
            'available_seats': str(event.available_seats),
            'weather_forecast': event.weather_forecast or 'Partly Cloudy, 28°C',
            'crowd_expectation': 'High',
            'gate_occupancy': 'Gate A: 75%, Gate B: 60%, Gate C: 45%'
        }
    except Event.DoesNotExist:
        # Fallback to mock data
        event_data = {
            'id': event_id,
            'name': 'India vs Australia',
            'date': '2025-11-05',
            'time': '18:00',
            'stadium': 'Chinnaswamy Stadium',
            'ticket_price': '₹2500',
            'available_seats': '1200',
            'weather_forecast': 'Partly Cloudy, 28°C',
            'crowd_expectation': 'High',
            'gate_occupancy': 'Gate A: 75%, Gate B: 60%, Gate C: 45%'
        }
    
    subscription_status = False
    if request.user.is_authenticated:
        from user.models import NotificationSubscription
        subscription_status = NotificationSubscription.objects.filter(
            user=request.user, event_id=event_id
        ).exists()
    
    return render(request, 'website/events_detail.html', {
        'page_title': f'{event_data["name"]} - Match Details',
        'event': event_data,
        'subscription_status': subscription_status
    })

# Page 6: Seat Selection
def seat_selection(request, event_id):
    """Seat selection page - accessible without login"""
    if request.user.is_authenticated and not request.user.is_verified:
        messages.info(request, 'You can browse seats, but please verify your identity to complete booking.')
    
    try:
        event = Event.objects.get(id=event_id, is_active=True)
        event_data = {
            'id': event.id,
            'name': event.name,
            'date': event.date.strftime('%Y-%m-%d'),
            'time': event.time.strftime('%H:%M'),
            'stadium': event.stadium,
            'ticket_price': float(event.ticket_price)
        }
    except Event.DoesNotExist:
        event_data = {
            'id': event_id,
            'name': 'India vs Australia',
            'date': '2025-11-05',
            'time': '18:00',
            'stadium': 'Chinnaswamy Stadium',
            'ticket_price': 2500.0
        }
    
    # Get seat map
    seat_map = {
        'blocks': [
            {'name': 'A', 'rows': 10, 'seats_per_row': 20},
            {'name': 'B', 'rows': 8, 'seats_per_row': 25},
            {'name': 'C', 'rows': 6, 'seats_per_row': 30}
        ]
    }
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to proceed with booking.')
            request.session['redirect_after_login'] = request.path
            return redirect('signup_login')
        if request.user.is_authenticated and not request.user.is_verified:
            messages.warning(request, 'Please verify your identity to complete booking.')
            return redirect('verify_identity')
        selected_seats = request.POST.getlist('selected_seats')
        if selected_seats:
            # Store selected seats in session
            request.session['selected_seats'] = selected_seats
            request.session['event_id'] = event_id
            return redirect('payment', event_id=event_id)
        else:
            messages.error(request, 'Please select at least one seat.')
    
    return render(request, 'website/seat_selection.html', {
        'page_title': f'Select Your Seats for {event_data["name"]}',
        'event': event_data,
        'seat_map': seat_map
    })

# Page 7: Payment
def payment(request, event_id):
    """Payment page - shows demo data if not logged in"""
    # Demo data for non-logged-in users
    demo_selected_seats = ['A-5-12', 'A-5-13', 'A-5-14']
    
    if not request.user.is_authenticated:
        # Show demo payment page
        try:
            event = Event.objects.get(id=event_id, is_active=True)
            ticket_price = float(event.ticket_price)
            event_data = {
                'id': event.id,
                'name': event.name,
                'date': event.date.strftime('%Y-%m-%d'),
                'time': event.time.strftime('%H:%M'),
                'stadium': event.stadium,
                'ticket_price': ticket_price
            }
        except Event.DoesNotExist:
            ticket_price = 2500.0
            event_data = {
                'id': event_id,
                'name': 'India vs Australia',
                'date': '2025-11-05',
                'time': '18:00',
                'stadium': 'Chinnaswamy Stadium',
                'ticket_price': ticket_price
            }
        
        total_price = len(demo_selected_seats) * ticket_price
        return render(request, 'website/payment.html', {
            'page_title': f'Review & Pay for {event_data["name"]} (Demo)',
            'event': event_data,
            'selected_seats': demo_selected_seats,
            'total_price': total_price,
            'is_demo': True
        })
    
    if not request.user.is_verified:
        messages.warning(request, 'Please verify your identity to complete booking.')
        return redirect('verify_identity')
    
    selected_seats = request.session.get('selected_seats', [])
    if not selected_seats:
        messages.error(request, 'No seats selected. Please select seats first.')
        return redirect('seat_selection', event_id=event_id)
    
    try:
        event = Event.objects.get(id=event_id, is_active=True)
        ticket_price = float(event.ticket_price)
        event_data = {
            'id': event.id,
            'name': event.name,
            'date': event.date.strftime('%Y-%m-%d'),
            'time': event.time.strftime('%H:%M'),
            'stadium': event.stadium,
            'ticket_price': ticket_price
        }
    except Event.DoesNotExist:
        ticket_price = 2500.0
        event_data = {
            'id': event_id,
            'name': 'India vs Australia',
            'date': '2025-11-05',
            'time': '18:00',
            'stadium': 'Chinnaswamy Stadium',
            'ticket_price': ticket_price
        }
    
    total_price = len(selected_seats) * ticket_price
    
    if request.method == 'POST':
        # Process payment (mock for now)
        # In production, integrate with Razorpay
        payment_method = request.POST.get('payment_method')
        if payment_method:
            # Mock successful payment
            messages.success(request, 'Payment successful! Redirecting to confirmation...')
            return redirect('ticket_confirmation')
        else:
            messages.error(request, 'Please select a payment method.')
    
    return render(request, 'website/payment.html', {
        'page_title': f'Review & Pay for {event_data["name"]}',
        'event': event_data,
        'selected_seats': selected_seats,
        'total_price': total_price,
        'is_demo': False
    })

# Page 8: Ticket Confirmation
def ticket_confirmation(request):
    """Ticket confirmation page - shows demo data if not logged in"""
    if not request.user.is_authenticated:
        # Show demo confirmation
        booking_data = {
            'id': 1,
            'event_name': 'India vs Australia',
            'date': '2025-11-05',
            'time': '18:00',
            'stadium': 'Chinnaswamy Stadium',
            'seat_block': 'A',
            'row': 5,
            'seat_number': 12,
            'entry_time_slot': '17:00-17:30',
            'qr_code_url': 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=GOVVENS-TICKET-CONFIRMED-001'
        }
        return render(request, 'website/ticket_confirmation.html', {
            'page_title': 'Ticket Confirmed! (Demo)',
            'booking': booking_data,
            'is_demo': True
        })
    
    selected_seats = request.session.get('selected_seats', [])
    event_id = request.session.get('event_id')
    
    if not selected_seats or not event_id:
        messages.error(request, 'No booking found.')
        return redirect('events_list')
    
    try:
        event = Event.objects.get(id=event_id)
        # Create booking records (mock for now)
        booking_data = {
            'id': 1,
            'event_name': event.name,
            'date': event.date.strftime('%Y-%m-%d'),
            'time': event.time.strftime('%H:%M'),
            'stadium': event.stadium,
            'seat_block': 'A',
            'row': 5,
            'seat_number': 12,
            'entry_time_slot': '17:00-17:30',
            'qr_code_url': 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=GOVVENS-TICKET-' + str(event_id)
        }
    except Event.DoesNotExist:
        booking_data = {
            'id': 1,
            'event_name': 'India vs Australia',
            'date': '2025-11-05',
            'time': '18:00',
            'stadium': 'Chinnaswamy Stadium',
            'seat_block': 'A',
            'row': 5,
            'seat_number': 12,
            'entry_time_slot': '17:00-17:30',
            'qr_code_url': 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=GOVVENS-TICKET-001'
        }
    
    # Clear session data
    if 'selected_seats' in request.session:
        del request.session['selected_seats']
    if 'event_id' in request.session:
        del request.session['event_id']
    
    return render(request, 'website/ticket_confirmation.html', {
        'page_title': 'Ticket Confirmed!',
        'booking': booking_data,
        'is_demo': False
    })

# Page 9: My Tickets
def my_tickets(request):
    """My tickets page - shows demo data for non-logged-in users"""
    if not request.user.is_authenticated:
        # Show demo data for non-logged-in users
        demo_bookings = [
            {
                'id': 1,
                'event_name': 'India vs Australia',
                'date': '2025-11-05',
                'time': '18:00',
                'seat_block': 'A',
                'row': 5,
                'seat_number': 12,
                'entry_time_slot': '17:00-17:30',
                'qr_code_url': 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=GOVVENS-TICKET-001'
            },
            {
                'id': 2,
                'event_name': 'IPL Final',
                'date': '2025-11-10',
                'time': '19:00',
                'seat_block': 'VIP',
                'row': 1,
                'seat_number': 5,
                'entry_time_slot': '18:00-18:30',
                'qr_code_url': 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=GOVVENS-TICKET-002'
            },
            {
                'id': 3,
                'event_name': 'T20 World Cup Match',
                'date': '2025-11-15',
                'time': '17:30',
                'seat_block': 'B',
                'row': 8,
                'seat_number': 20,
                'entry_time_slot': '16:30-17:00',
                'qr_code_url': 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=GOVVENS-TICKET-003'
            }
        ]
        return render(request, 'website/my_tickets.html', {
            'page_title': 'My Booked Tickets (Demo)',
            'bookings': demo_bookings,
            'is_demo': True
        })
    
    # For logged-in users, show their actual bookings
    bookings = Booking.objects.filter(user=request.user, payment_status='SUCCESS').order_by('-booking_time')
    
    if bookings.exists():
        bookings_data = [{
            'id': b.id,
            'event_name': b.event.name,
            'date': b.event.date.strftime('%Y-%m-%d'),
            'time': b.event.time.strftime('%H:%M'),
            'seat_block': b.seat_block,
            'row': b.row,
            'seat_number': b.seat_number,
            'entry_time_slot': b.entry_time_slot or '17:00-17:30',
            'qr_code_url': b.qr_code or 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=GOVVENS-TICKET-' + str(b.id)
        } for b in bookings]
    else:
        # Show demo data if user has no bookings
        bookings_data = [
            {
                'id': 1,
                'event_name': 'India vs Australia',
                'date': '2025-11-05',
                'time': '18:00',
                'seat_block': 'A',
                'row': 5,
                'seat_number': 12,
                'entry_time_slot': '17:00-17:30',
                'qr_code_url': 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=GOVVENS-TICKET-001'
            }
        ]
    
    return render(request, 'website/my_tickets.html', {
        'page_title': 'My Booked Tickets',
        'bookings': bookings_data,
        'is_demo': False
    })

# Page 11: Map and Entry/Exit Plan
def entry_exit_plan(request):
    """Map and entry/exit plan page - accessible without login"""
    user_pin = request.user.pin_code if request.user.is_authenticated else '560001'
    return render(request, 'website/map_entry_exit.html', {
        'page_title': 'Plan Your Journey to the Stadium',
        'user_pin': user_pin,
        'departure_time': '17:00',
        'entry_window': '17:00-17:30'
    })

# Page 12: Exit Info
def exit_info(request):
    """Exit info page"""
    return render(request, 'website/exit_info.html', {
        'page_title': 'Exit Instructions',
        'exit_gate': 'Gate B',
        'exit_time_window': '21:30-22:00',
        'egress_route': 'Follow signs to Gate B, avoid central concourse.'
    })

# FAQ Page
def faq_page(request):
    """FAQ page with all user questions"""
    faqs = [
        {
            'question': 'What is Govvens?',
            'answer': 'Govvens is a civic-tech ticketing and crowd-safety platform that manages crowd entry, ticketing, and exit for large events using staggered timings and verified ticketing. We ensure safe, organized, and fair access to high-footfall cricket events at venues like Chinnaswamy Stadium.',
            'icon': 'bi-info-circle',
            'category': 'general'
        },
        {
            'question': 'How does the notification system work?',
            'answer': 'Users pay a small, refundable fee (₹10) to get SMS alerts when tickets for specific matches open. This ensures fair and early access. The fee is deductible from your ticket price when you make a booking. You\'ll receive timely notifications via SMS and email before tickets go on sale.',
            'icon': 'bi-bell',
            'category': 'notifications'
        },
        {
            'question': 'How are tickets verified?',
            'answer': 'Each ticket is tied to the user through Aadhaar-based eKYC and facial recognition. At the venue, you\'ll go through a quick face/eye scan similar to DigiYatra. Backup verification uses mobile OTP and ID at entry gates if needed. This ensures secure entry and prevents ticket fraud.',
            'icon': 'bi-shield-check',
            'category': 'verification'
        },
        {
            'question': 'How is crowd control managed?',
            'answer': 'The system assigns specific time slots for entry and exit through automated SMS and app notifications, minimizing congestion and stampede risk. Each user gets a personalized entry window (e.g., 17:00-17:30) and exit window, ensuring staggered flow of crowds throughout the event.',
            'icon': 'bi-people',
            'category': 'crowd-control'
        },
        {
            'question': 'Do I need to share my live location?',
            'answer': 'No. Only your home PIN code is required. Routes and timings are computed using Google Maps API based on that. We calculate the best departure time from your location to arrive during your assigned entry window. Your privacy is protected - we never track your live location.',
            'icon': 'bi-geo-alt',
            'category': 'privacy'
        },
        {
            'question': 'Can I book seats for my friends or family?',
            'answer': 'Yes. The seat map supports individual, friends, and family bookings. You can select multiple seats together, and they will be held for up to 15 minutes during checkout. Each person will need their own identity verification for entry at the venue.',
            'icon': 'bi-people-fill',
            'category': 'booking'
        },
        {
            'question': 'How do I pay for tickets?',
            'answer': 'Payments are processed securely via Razorpay. We accept Credit Cards, Debit Cards, UPI, Net Banking, and Wallets. All transactions are encrypted and secure. You\'ll receive a payment confirmation and digital ticket with QR code immediately after successful payment.',
            'icon': 'bi-credit-card',
            'category': 'payment'
        },
        {
            'question': 'What if my payment fails?',
            'answer': 'The reserved seats are released after 15 minutes if payment isn\'t completed. You\'ll receive a notification if your payment fails. You can retry the payment within the 15-minute window. If the time expires, you\'ll need to select seats again. We recommend having a backup payment method ready.',
            'icon': 'bi-exclamation-triangle',
            'category': 'payment'
        },
    ]
    return render(request, 'website/faq.html', {
        'page_title': 'Frequently Asked Questions',
        'faqs': faqs
    })

# Dashboard - Superuser Only
def is_superuser(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_superuser, login_url='/')
def dashboard(request):
    """Admin dashboard for managing users - Superuser only"""
    # Get all users
    users = User.objects.all().order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Filter functionality
    filter_type = request.GET.get('filter', '')
    if filter_type == 'verified':
        users = users.filter(is_verified=True)
    elif filter_type == 'unverified':
        users = users.filter(is_verified=False)
    elif filter_type == 'active':
        users = users.filter(is_active=True)
    elif filter_type == 'inactive':
        users = users.filter(is_active=False)
    elif filter_type == 'staff':
        users = users.filter(is_staff=True)
    elif filter_type == 'superuser':
        users = users.filter(is_superuser=True)
    
    # Sorting
    sort_by = request.GET.get('sort', '-date_joined')
    if sort_by in ['email', 'username', 'date_joined', '-date_joined', '-email', '-username']:
        users = users.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(users, 25)  # Show 25 users per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_users = User.objects.count()
    verified_users = User.objects.filter(is_verified=True).count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    recent_users = User.objects.filter(date_joined__gte=timezone.now() - timezone.timedelta(days=7)).count()
    
    context = {
        'page_title': 'Admin Dashboard - User Management',
        'users': page_obj,
        'total_users': total_users,
        'verified_users': verified_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'recent_users': recent_users,
        'search_query': search_query,
        'filter_type': filter_type,
        'sort_by': sort_by,
    }
    
    return render(request, 'website/dashboard.html', context)

@login_required
@user_passes_test(is_superuser, login_url='/')
def delete_user(request, user_id):
    """Delete a user - Superuser only"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            # Prevent deleting yourself
            if user.id == request.user.id:
                messages.error(request, 'You cannot delete your own account!')
            else:
                user_email = user.email
                user.delete()
                messages.success(request, f'User {user_email} has been deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
    return redirect('dashboard')

@login_required
@user_passes_test(is_superuser, login_url='/')
def toggle_user_status(request, user_id):
    """Toggle user active status - Superuser only"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            # Prevent deactivating yourself
            if user.id == request.user.id:
                messages.error(request, 'You cannot deactivate your own account!')
            else:
                user.is_active = not user.is_active
                user.save()
                status = 'activated' if user.is_active else 'deactivated'
                messages.success(request, f'User {user.email} has been {status}.')
        except Exception as e:
            messages.error(request, f'Error updating user status: {str(e)}')
    return redirect('dashboard')

@login_required
@user_passes_test(is_superuser, login_url='/')
def export_users_excel(request):
    """Export users to Excel - Superuser only"""
    # Get all users with filters applied
    users = User.objects.all().order_by('-date_joined')
    
    # Apply search filter if exists
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Apply filter if exists
    filter_type = request.GET.get('filter', '')
    if filter_type == 'verified':
        users = users.filter(is_verified=True)
    elif filter_type == 'unverified':
        users = users.filter(is_verified=False)
    elif filter_type == 'active':
        users = users.filter(is_active=True)
    elif filter_type == 'inactive':
        users = users.filter(is_active=False)
    elif filter_type == 'staff':
        users = users.filter(is_staff=True)
    elif filter_type == 'superuser':
        users = users.filter(is_superuser=True)
    
    # Create workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Users Data"
    
    # Header row
    headers = ['ID', 'Email', 'Username', 'First Name', 'Last Name', 'Phone', 'PIN Code', 
               'Date of Birth', 'Gender', 'Verified', 'Active', 'Staff', 'Superuser', 
               'Date Joined', 'Last Login']
    
    # Style header row
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Data rows
    for row_num, user in enumerate(users, 2):
        ws.cell(row=row_num, column=1, value=user.id)
        ws.cell(row=row_num, column=2, value=user.email)
        ws.cell(row=row_num, column=3, value=user.username)
        ws.cell(row=row_num, column=4, value=user.first_name or '')
        ws.cell(row=row_num, column=5, value=user.last_name or '')
        ws.cell(row=row_num, column=6, value=user.phone or '')
        ws.cell(row=row_num, column=7, value=user.pin_code or '')
        ws.cell(row=row_num, column=8, value=user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else '')
        ws.cell(row=row_num, column=9, value=user.get_gender_display() if user.gender else '')
        ws.cell(row=row_num, column=10, value='Yes' if user.is_verified else 'No')
        ws.cell(row=row_num, column=11, value='Yes' if user.is_active else 'No')
        ws.cell(row=row_num, column=12, value='Yes' if user.is_staff else 'No')
        ws.cell(row=row_num, column=13, value='Yes' if user.is_superuser else 'No')
        ws.cell(row=row_num, column=14, value=user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '')
        ws.cell(row=row_num, column=15, value=user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never')
    
    # Auto-adjust column widths
    for col_num, header in enumerate(headers, 1):
        column_letter = get_column_letter(col_num)
        max_length = max(
            len(str(header)),
            max((len(str(ws.cell(row=row_num, column=col_num).value)) for row_num in range(2, ws.max_row + 1)), default=0)
        )
        ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
    
    # Create HTTP response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response

# UserSession Management Views
@login_required
@user_passes_test(is_superuser, login_url='/')
def dashboard_sessions(request):
    """User Sessions Dashboard - Superuser only"""
    sessions = UserSession.objects.select_related('user').prefetch_related('activities').all().order_by('-started_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        sessions = sessions.filter(
            Q(session_id__icontains=search_query) |
            Q(visitor_id__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(ip_address__icontains=search_query) |
            Q(country__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(browser__icontains=search_query) |
            Q(os__icontains=search_query)
        )
    
    # Filter functionality
    filter_type = request.GET.get('filter', '')
    if filter_type == 'authenticated':
        sessions = sessions.filter(is_authenticated=True)
    elif filter_type == 'anonymous':
        sessions = sessions.filter(is_authenticated=False)
    elif filter_type == 'active':
        sessions = sessions.filter(ended_at__isnull=True)
    elif filter_type == 'ended':
        sessions = sessions.filter(ended_at__isnull=False)
    elif filter_type == 'bot':
        sessions = sessions.filter(is_bot=True)
    elif filter_type == 'desktop':
        sessions = sessions.filter(device_type='desktop')
    elif filter_type == 'mobile':
        sessions = sessions.filter(device_type='mobile')
    elif filter_type == 'tablet':
        sessions = sessions.filter(device_type='tablet')
    
    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        try:
            sessions = sessions.filter(started_at__gte=parse_date(date_from))
        except:
            pass
    if date_to:
        try:
            sessions = sessions.filter(started_at__lte=parse_date(date_to))
        except:
            pass
    
    # User filter
    user_id = request.GET.get('user_id', '')
    if user_id:
        sessions = sessions.filter(user_id=user_id)
    
    # Sorting
    sort_by = request.GET.get('sort', '-started_at')
    if sort_by in ['started_at', '-started_at', 'last_activity_at', '-last_activity_at', 'duration_seconds', '-duration_seconds']:
        sessions = sessions.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(sessions, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_sessions = UserSession.objects.count()
    authenticated_sessions = UserSession.objects.filter(is_authenticated=True).count()
    anonymous_sessions = UserSession.objects.filter(is_authenticated=False).count()
    active_sessions = UserSession.objects.filter(ended_at__isnull=True).count()
    bot_sessions = UserSession.objects.filter(is_bot=True).count()
    
    # Device type stats
    device_stats = UserSession.objects.values('device_type').annotate(count=Count('id')).order_by('-count')
    
    # Country stats
    top_countries = UserSession.objects.exclude(country='').values('country').annotate(count=Count('id')).order_by('-count')[:10]
    
    # Average session duration
    ended_sessions = UserSession.objects.filter(ended_at__isnull=False)
    avg_duration = None
    if ended_sessions.exists():
        durations = [s.duration_seconds for s in ended_sessions]
        avg_duration = sum(durations) / len(durations) if durations else 0
    
    context = {
        'page_title': 'Admin Dashboard - User Sessions',
        'sessions': page_obj,
        'total_sessions': total_sessions,
        'authenticated_sessions': authenticated_sessions,
        'anonymous_sessions': anonymous_sessions,
        'active_sessions': active_sessions,
        'bot_sessions': bot_sessions,
        'device_stats': device_stats,
        'top_countries': top_countries,
        'avg_duration': avg_duration,
        'search_query': search_query,
        'filter_type': filter_type,
        'sort_by': sort_by,
        'date_from': date_from,
        'date_to': date_to,
        'user_id': user_id,
    }
    
    return render(request, 'website/dashboard_sessions.html', context)

@login_required
@user_passes_test(is_superuser, login_url='/')
def session_detail(request, session_id):
    """Detailed view of a user session - Superuser only"""
    session = get_object_or_404(UserSession.objects.select_related('user').prefetch_related('activities'), id=session_id)
    
    # Get all activities for stats
    all_activities = session.activities.all()

    # Get activities for this session
    activities = all_activities.order_by('-timestamp')[:100]  # Limit to 100 most recent
    
    # Statistics
    activity_stats = all_activities.values('event_type').annotate(count=Count('id')).order_by('-count')
    
    # Response time stats
    response_times = all_activities.exclude(response_time_ms__isnull=True)
    avg_response_time = response_times.aggregate(Avg('response_time_ms'))['response_time_ms__avg']
    
    context = {
        'page_title': f'Session Details - {session.session_id[:20]}...',
        'session': session,
        'activities': activities,
        'activity_stats': activity_stats,
        'avg_response_time': avg_response_time,
        'total_activities': session.activities.count(),
    }
    
    return render(request, 'website/session_detail.html', context)

@login_required
@user_passes_test(is_superuser, login_url='/')
def delete_session(request, session_id):
    """Delete a session - Superuser only"""
    if request.method == 'POST':
        try:
            session = get_object_or_404(UserSession, id=session_id)
            session_id_str = session.session_id
            session.delete()
            messages.success(request, f'Session {session_id_str[:20]}... has been deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting session: {str(e)}')
    return redirect('dashboard_sessions')

@login_required
@user_passes_test(is_superuser, login_url='/')
def export_sessions_excel(request):
    """Export sessions to Excel - Superuser only"""
    sessions = UserSession.objects.select_related('user').all().order_by('-started_at')
    
    # Apply filters
    search_query = request.GET.get('search', '')
    if search_query:
        sessions = sessions.filter(
            Q(session_id__icontains=search_query) |
            Q(visitor_id__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(ip_address__icontains=search_query)
        )
    
    filter_type = request.GET.get('filter', '')
    if filter_type == 'authenticated':
        sessions = sessions.filter(is_authenticated=True)
    elif filter_type == 'anonymous':
        sessions = sessions.filter(is_authenticated=False)
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sessions Data"
    
    headers = ['ID', 'Session ID', 'Visitor ID', 'User Email', 'User Username', 'Authenticated', 
               'IP Address', 'Country', 'City', 'Device Type', 'Browser', 'OS', 
               'Started At', 'Last Activity', 'Ended At', 'Duration (seconds)', 'Is Bot', 'Activities Count']
    
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for row_num, session in enumerate(sessions, 2):
        ws.cell(row=row_num, column=1, value=session.id)
        ws.cell(row=row_num, column=2, value=session.session_id)
        ws.cell(row=row_num, column=3, value=str(session.visitor_id))
        ws.cell(row=row_num, column=4, value=session.user.email if session.user else 'Anonymous')
        ws.cell(row=row_num, column=5, value=session.user.username if session.user else '')
        ws.cell(row=row_num, column=6, value='Yes' if session.is_authenticated else 'No')
        ws.cell(row=row_num, column=7, value=str(session.ip_address) if session.ip_address else '')
        ws.cell(row=row_num, column=8, value=session.country or '')
        ws.cell(row=row_num, column=9, value=session.city or '')
        ws.cell(row=row_num, column=10, value=session.get_device_type_display())
        ws.cell(row=row_num, column=11, value=session.browser or '')
        ws.cell(row=row_num, column=12, value=session.os or '')
        ws.cell(row=row_num, column=13, value=session.started_at.strftime('%Y-%m-%d %H:%M:%S') if session.started_at else '')
        ws.cell(row=row_num, column=14, value=session.last_activity_at.strftime('%Y-%m-%d %H:%M:%S') if session.last_activity_at else '')
        ws.cell(row=row_num, column=15, value=session.ended_at.strftime('%Y-%m-%d %H:%M:%S') if session.ended_at else 'Active')
        ws.cell(row=row_num, column=16, value=session.duration_seconds)
        ws.cell(row=row_num, column=17, value='Yes' if session.is_bot else 'No')
        ws.cell(row=row_num, column=18, value=session.activities.count())
    
    # Auto-adjust column widths
    for col_num, header in enumerate(headers, 1):
        column_letter = get_column_letter(col_num)
        max_length = max(
            len(str(header)),
            max((len(str(ws.cell(row=row_num, column=col_num).value or '')) for row_num in range(2, ws.max_row + 1)), default=0)
        )
        ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'sessions_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response

# UserActivity Management Views
@login_required
@user_passes_test(is_superuser, login_url='/')
def dashboard_activities(request):
    """User Activities Dashboard - Superuser only"""
    activities = UserActivity.objects.select_related('session', 'session__user').all().order_by('-timestamp')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        activities = activities.filter(
            Q(path__icontains=search_query) |
            Q(url__icontains=search_query) |
            Q(view_name__icontains=search_query) |
            Q(session__user__email__icontains=search_query) |
            Q(session__session_id__icontains=search_query) |
            Q(client_ip__icontains=search_query)
        )
    
    # Filter functionality
    filter_type = request.GET.get('filter', '')
    if filter_type == 'page_view':
        activities = activities.filter(event_type='page_view')
    elif filter_type == 'api_request':
        activities = activities.filter(event_type='api_request')
    elif filter_type == 'interaction':
        activities = activities.filter(event_type='interaction')
    elif filter_type == 'auth':
        activities = activities.filter(event_type='auth')
    elif filter_type == 'custom':
        activities = activities.filter(event_type='custom_event')
    
    # Status code filter
    status_code = request.GET.get('status_code', '')
    if status_code:
        activities = activities.filter(status_code=status_code)
    
    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        try:
            activities = activities.filter(timestamp__gte=parse_date(date_from))
        except:
            pass
    if date_to:
        try:
            activities = activities.filter(timestamp__lte=parse_date(date_to))
        except:
            pass
    
    # Session filter
    session_id = request.GET.get('session_id', '')
    if session_id:
        activities = activities.filter(session_id=session_id)
    
    # User filter
    user_id = request.GET.get('user_id', '')
    if user_id:
        activities = activities.filter(session__user_id=user_id)
    
    # Sorting
    sort_by = request.GET.get('sort', '-timestamp')
    if sort_by in ['timestamp', '-timestamp', 'response_time_ms', '-response_time_ms']:
        activities = activities.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_activities = UserActivity.objects.count()
    page_views = UserActivity.objects.filter(event_type='page_view').count()
    api_requests = UserActivity.objects.filter(event_type='api_request').count()
    interactions = UserActivity.objects.filter(event_type='interaction').count()
    auth_events = UserActivity.objects.filter(event_type='auth').count()
    
    # Event type stats
    event_type_stats = UserActivity.objects.values('event_type').annotate(count=Count('id')).order_by('-count')
    
    # Status code stats
    status_code_stats = UserActivity.objects.exclude(status_code__isnull=True).values('status_code').annotate(count=Count('id')).order_by('-status_code')[:20]
    
    # Average response time
    response_times = UserActivity.objects.exclude(response_time_ms__isnull=True)
    avg_response_time = response_times.aggregate(Avg('response_time_ms'))['response_time_ms__avg']
    
    context = {
        'page_title': 'Admin Dashboard - User Activities',
        'activities': page_obj,
        'total_activities': total_activities,
        'page_views': page_views,
        'api_requests': api_requests,
        'interactions': interactions,
        'auth_events': auth_events,
        'event_type_stats': event_type_stats,
        'status_code_stats': status_code_stats,
        'avg_response_time': avg_response_time,
        'search_query': search_query,
        'filter_type': filter_type,
        'status_code': status_code,
        'sort_by': sort_by,
        'date_from': date_from,
        'date_to': date_to,
        'session_id': session_id,
        'user_id': user_id,
    }
    
    return render(request, 'website/dashboard_activities.html', context)

@login_required
@user_passes_test(is_superuser, login_url='/')
def activity_detail(request, activity_id):
    """Detailed view of a user activity - Superuser only"""
    activity = get_object_or_404(UserActivity.objects.select_related('session', 'session__user'), id=activity_id)
    
    # Format JSON fields for display
    query_params_json = json.dumps(activity.query_params, indent=2) if activity.query_params else None
    payload_json = json.dumps(activity.payload, indent=2) if activity.payload else None
    metadata_json = json.dumps(activity.metadata, indent=2) if activity.metadata else None
    
    context = {
        'page_title': f'Activity Details - {activity.event_type}',
        'activity': activity,
        'query_params_json': query_params_json,
        'payload_json': payload_json,
        'metadata_json': metadata_json,
    }
    
    return render(request, 'website/activity_detail.html', context)

@login_required
@user_passes_test(is_superuser, login_url='/')
def delete_activity(request, activity_id):
    """Delete an activity - Superuser only"""
    if request.method == 'POST':
        try:
            activity = get_object_or_404(UserActivity, id=activity_id)
            activity_path = activity.path
            activity.delete()
            messages.success(request, f'Activity {activity_path} has been deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting activity: {str(e)}')
    return redirect('dashboard_activities')

@login_required
@user_passes_test(is_superuser, login_url='/')
def export_activities_excel(request):
    """Export activities to Excel - Superuser only"""
    activities = UserActivity.objects.select_related('session', 'session__user').all().order_by('-timestamp')
    
    # Apply filters
    search_query = request.GET.get('search', '')
    if search_query:
        activities = activities.filter(
            Q(path__icontains=search_query) |
            Q(session__user__email__icontains=search_query)
        )
    
    filter_type = request.GET.get('filter', '')
    if filter_type:
        activities = activities.filter(event_type=filter_type)
    
    # Limit to prevent memory issues
    activities = activities[:10000]
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Activities Data"
    
    headers = ['ID', 'Event Type', 'Path', 'URL', 'Method', 'Status Code', 'Response Time (ms)',
               'Session ID', 'User Email', 'User Username', 'Client IP', 'Country', 
               'View Name', 'Handler', 'Timestamp', 'Referrer']
    
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for row_num, activity in enumerate(activities, 2):
        ws.cell(row=row_num, column=1, value=activity.id)
        ws.cell(row=row_num, column=2, value=activity.get_event_type_display())
        ws.cell(row=row_num, column=3, value=activity.path[:100] if activity.path else '')
        ws.cell(row=row_num, column=4, value=activity.url[:200] if activity.url else '')
        ws.cell(row=row_num, column=5, value=activity.method or '')
        ws.cell(row=row_num, column=6, value=activity.status_code or '')
        ws.cell(row=row_num, column=7, value=activity.response_time_ms or '')
        ws.cell(row=row_num, column=8, value=activity.session.session_id if activity.session else '')
        ws.cell(row=row_num, column=9, value=activity.session.user.email if activity.session and activity.session.user else 'Anonymous')
        ws.cell(row=row_num, column=10, value=activity.session.user.username if activity.session and activity.session.user else '')
        ws.cell(row=row_num, column=11, value=str(activity.client_ip) if activity.client_ip else '')
        ws.cell(row=row_num, column=12, value=activity.country or '')
        ws.cell(row=row_num, column=13, value=activity.view_name or '')
        ws.cell(row=row_num, column=14, value=activity.handler or '')
        ws.cell(row=row_num, column=15, value=activity.timestamp.strftime('%Y-%m-%d %H:%M:%S') if activity.timestamp else '')
        ws.cell(row=row_num, column=16, value=activity.referrer[:200] if activity.referrer else '')
    
    # Auto-adjust column widths
    for col_num, header in enumerate(headers, 1):
        column_letter = get_column_letter(col_num)
        max_length = max(
            len(str(header)),
            max((len(str(ws.cell(row=row_num, column=col_num).value or '')) for row_num in range(2, ws.max_row + 1)), default=0)
        )
        ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'activities_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response