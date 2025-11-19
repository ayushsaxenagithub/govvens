from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event, Booking

# Page 1: Landing Page (Static)
def landing_page(request):
    """Static landing page for investor presentation"""
    return render(request, 'website/landing.html', {
        'page_title': 'GOVVENS - Crowd-Safe Ticketing',
        'hero_title': 'Welcome to GOVVENS',
        'hero_subtitle': 'Crowd-safe ticketing for high-footfall cricket events at Chinnaswamy Stadium.',
        'featured_events': [
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
            }
        ]
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