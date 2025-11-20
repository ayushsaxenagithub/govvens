"""
Custom error handlers for 404 and 500 errors
"""
from django.shortcuts import render
from django.template import RequestContext

def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, '404.html', status=404)

def handler500(request):
    """Custom 500 error handler"""
    return render(request, '500.html', status=500)

