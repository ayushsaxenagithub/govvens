from django.urls import path
from . import views

urlpatterns = [
    # Page 2: Signup / Login
    path('signup-login/', views.signup_login, name='signup_login'),

    # Page 3: User Verification (Face/Eye Scan)
    path('verify-identity/', views.verify_identity, name='verify_identity'),

    # Logout
    path('logout/', views.user_logout, name='user_logout'),

    # Page 10: Entry Verification (At Venue)
    path('entry-verification/', views.entry_verification, name='entry_verification'),

    # Page 13: Operator Dashboard
    path('operator-dashboard/', views.operator_dashboard, name='operator_dashboard'),
]