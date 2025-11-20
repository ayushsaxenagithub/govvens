from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import User, NotificationSubscription
import random

# Page 2: Signup / Login
def signup_login(request):
    if request.method == 'POST':
        action = request.POST.get('action')  # 'signup' or 'login'
        email = request.POST.get('email')
        password = request.POST.get('password')
        username = request.POST.get('username', '')
        phone = request.POST.get('phone', '')
        pin_code = request.POST.get('pin_code', '')
        
        if action == 'signup':
            # Signup logic
            if not email:
                messages.error(request, 'Email address is required.')
            elif not username:
                messages.error(request, 'Username is required.')
            elif not password:
                messages.error(request, 'Password is required.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'An account with this email already exists. Please login instead.')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'This username is already taken. Please choose another.')
            elif len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            else:
                try:
                    # Clean phone and pin_code - set to None if empty
                    phone_value = phone.strip() if phone and phone.strip() else None
                    pin_code_value = pin_code.strip() if pin_code and pin_code.strip() else None
                    
                    # Create user
                    user = User.objects.create_user(
                        username=username.strip(),
                        email=email.strip().lower(),
                        password=password,
                        phone=phone_value,
                        pin_code=pin_code_value
                    )
                    login(request, user)
                    messages.success(request, 'Account created successfully! Welcome to GOVVENS.')
                    # Redirect to intended page if exists
                    redirect_url = request.session.get('redirect_after_login', 'events_list')
                    if 'redirect_after_login' in request.session:
                        del request.session['redirect_after_login']
                    return redirect(redirect_url)
                except Exception as e:
                    messages.error(request, f'Error creating account: {str(e)}')
        
        elif action == 'login':
            # Login logic
            if email and password:
                # Try authenticating with email (since USERNAME_FIELD is email)
                try:
                    user = User.objects.get(email=email)
                    if user.check_password(password):
                        login(request, user)
                        messages.success(request, f'Welcome back, {user.email}!')
                        # Redirect to intended page if exists
                        redirect_url = request.session.get('redirect_after_login', 'events_list')
                        if 'redirect_after_login' in request.session:
                            del request.session['redirect_after_login']
                        return redirect(redirect_url)
                    else:
                        messages.error(request, 'Invalid email or password. Please try again.')
                except User.DoesNotExist:
                    # Also try standard authenticate as fallback
                    user = authenticate(request, username=email, password=password)
                    if user is not None:
                        login(request, user)
                        messages.success(request, f'Welcome back, {user.email}!')
                        # Redirect to intended page if exists
                        redirect_url = request.session.get('redirect_after_login', 'events_list')
                        if 'redirect_after_login' in request.session:
                            del request.session['redirect_after_login']
                        return redirect(redirect_url)
                    else:
                        messages.error(request, 'Invalid email or password. Please try again.')
            else:
                messages.error(request, 'Please enter both email and password.')
    
    return render(request, 'user/signup_login.html')

# Page 3: User Verification (Face/Eye Scan)
def verify_identity(request):
    if not request.user.is_authenticated:
        messages.info(request, 'Please login to verify your identity.')
        return redirect('signup_login')
    
    if request.method == 'POST':
        # Simulate face/eye scan success
        # In real app, integrate with eKYC provider or facial recognition API
        # For MVP, just mark user as verified
        request.user.is_verified = True
        request.user.save()
        messages.success(request, 'Identity verified successfully!')
        return redirect('events_list')
    return render(request, 'user/verify_identity.html')

# Page 10: Entry Verification (At Venue)
def entry_verification(request):
    # This page would be accessed at the venue gate
    # Verify user by scanning QR code or using face/eye scan
    # For MVP, mock verification
    if request.method == 'POST':
        qr_code = request.POST.get('qr_code')
        # Validate QR code (mock)
        if qr_code == 'VALID_QR_CODE':
            return JsonResponse({'status': 'success', 'message': 'Entry granted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid ticket'})

    # For testing, allow manual input
    return render(request, 'user/entry_verification.html')

# Logout
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing_page')

# Page 13: Operator Dashboard
def operator_dashboard(request):
    # Check if user is an operator (mock role check)
    if not request.user.is_staff:  # Assuming operators are staff users
        return HttpResponseForbidden("Access Denied")

    # Fetch real-time data: ticket sales, gate occupancy
    # Mock data for MVP
    from website.models import Booking, GateOccupancy
    total_tickets_sold = Booking.objects.filter(payment_status='SUCCESS').count()
    gates = GateOccupancy.objects.all()

    return render(request, 'user/operator_dashboard.html', {
        'total_tickets_sold': total_tickets_sold,
        'gates': gates,
        'current_time': timezone.now(),
    })