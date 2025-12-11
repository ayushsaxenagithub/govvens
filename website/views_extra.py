from django.http import HttpResponse
from django.shortcuts import render
from .models import Event

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /dashboard/",
        "Disallow: /ticket/confirm/",
        "Disallow: /my-tickets/",
        "Disallow: /payment/",
        "Allow: /",
        "Sitemap: https://govvens.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def rss_feed(request):
    events = Event.objects.filter(is_active=True).order_by('date')
    return render(request, 'website/rss_feed.xml', {'events': events}, content_type="application/rss+xml")
