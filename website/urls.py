from django.urls import path
from . import views

urlpatterns = [
    # Page 1: Landing Page
    path('', views.landing_page, name='landing_page'),

    # Page 4: Events List
    path('events/', views.events_list, name='events_list'),

    # Page 5: Event Details
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),

    # Page 6: Seat Selection
    path('event/<int:event_id>/seats/', views.seat_selection, name='seat_selection'),

    # Page 7: Payment
    path('event/<int:event_id>/payment/', views.payment, name='payment'),

    # Page 8: Ticket Confirmation (accessible directly for demo)
    path('ticket/confirm/', views.ticket_confirmation, name='ticket_confirmation'),
    path('ticket/demo/', views.ticket_confirmation, name='ticket_confirmation_demo'),

    # Page 9: My Tickets
    path('my-tickets/', views.my_tickets, name='my_tickets'),

    # Page 11: Map and Entry/Exit Plan
    path('entry-exit-plan/', views.entry_exit_plan, name='entry_exit_plan'),

    # Page 12: Exit Info
    path('exit-info/', views.exit_info, name='exit_info'),
    
    # FAQ Page
    path('faq/', views.faq_page, name='faq'),
]