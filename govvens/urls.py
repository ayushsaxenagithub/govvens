"""
URL configuration for govvens project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, Http404
import os

# Security file serving views
def serve_robots(request):
    """Serve robots.txt"""
    file_path = os.path.join(settings.BASE_DIR, 'static', 'robots.txt')
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/plain')
    raise Http404("robots.txt not found")

def serve_security_txt(request):
    """Serve security.txt"""
    file_path = os.path.join(settings.BASE_DIR, 'static', '.well-known', 'security.txt')
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/plain')
    raise Http404("security.txt not found")

def serve_sitemap(request):
    """Serve sitemap.xml"""
    file_path = os.path.join(settings.BASE_DIR, 'static', 'sitemap.xml')
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/xml')
    raise Http404("sitemap.xml not found")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('', include('website.urls')),
    
    # Security files
    path('robots.txt', serve_robots),
    path('security.txt', serve_security_txt),
    path('.well-known/security.txt', serve_security_txt),
    path('sitemap.xml', serve_sitemap),
]

# Serve static and media files
# Note: In production with DEBUG=False, you should use a web server (nginx/apache) 
# or install whitenoise. For now, we serve static files via Django in both modes.
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Always add staticfiles_urlpatterns for admin static files
urlpatterns += staticfiles_urlpatterns()

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error handlers
handler404 = 'govvens.views.handler404'
handler500 = 'govvens.views.handler500'

