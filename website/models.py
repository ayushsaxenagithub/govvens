from django.db import models
from django.utils import timezone
from user.models import User

class Event(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    stadium = models.CharField(max_length=255, default="Chinnaswamy Stadium")
    weather_forecast = models.TextField(blank=True, null=True)  # From API
    ticket_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_seats = models.IntegerField(default=0)
    available_seats = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} on {self.date} at {self.time}"

class SeatMap(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='seat_map')
    # For MVP: store seat map as JSON string (static layout)
    layout_json = models.JSONField(default=dict)  # e.g., {"blocks": [{"name": "A", "rows": 10, "seats_per_row": 20}]}

    def __str__(self):
        return f"Seat Map for {self.event.name}"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    seat_block = models.CharField(max_length=10)
    row = models.IntegerField()
    seat_number = models.IntegerField()
    booking_time = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ], default='PENDING')
    entry_time_slot = models.CharField(max_length=50, blank=True, null=True)  # e.g., "17:00-17:30"
    qr_code = models.CharField(max_length=255, blank=True, null=True)  # URL to QR image

    class Meta:
        unique_together = ('event', 'seat_block', 'row', 'seat_number')

    def __str__(self):
        return f"Booking {self.id} by {self.user.phone} for {self.event.name}"

class GateOccupancy(models.Model):
    gate_name = models.CharField(max_length=10)  # e.g., "Gate A"
    occupancy_percentage = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.gate_name}: {self.occupancy_percentage}%"