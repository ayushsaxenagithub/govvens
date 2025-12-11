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
    
    # Dashboard - Superuser Only
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('dashboard/toggle-user/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('dashboard/export-excel/', views.export_users_excel, name='export_users_excel'),
    
    # User Sessions Dashboard
    path('dashboard/sessions/', views.dashboard_sessions, name='dashboard_sessions'),
    path('dashboard/sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('dashboard/sessions/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('dashboard/sessions/export-excel/', views.export_sessions_excel, name='export_sessions_excel'),
    
    # User Activities Dashboard
    path('dashboard/activities/', views.dashboard_activities, name='dashboard_activities'),
    path('dashboard/activities/<int:activity_id>/', views.activity_detail, name='activity_detail'),
    path('dashboard/activities/<int:activity_id>/delete/', views.delete_activity, name='delete_activity'),
    path('dashboard/activities/export-excel/', views.export_activities_excel, name='export_activities_excel'),
]