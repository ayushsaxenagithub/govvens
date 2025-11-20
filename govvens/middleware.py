"""
Custom middleware to protect admin routes
"""
from django.shortcuts import redirect
from django.urls import resolve

class AdminProtectionMiddleware:
    """
    Middleware to protect /admin routes - only allows logged-in staff users
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request is for admin
        if request.path.startswith('/admin/'):
            # Allow access to admin login and logout pages
            if request.path in ['/admin/login/', '/admin/logout/']:
                response = self.get_response(request)
                return response
            
            # For all other admin pages, check if user is authenticated and is staff
            if not request.user.is_authenticated or not request.user.is_staff:
                return redirect('landing_page')
        
        response = self.get_response(request)
        return response

