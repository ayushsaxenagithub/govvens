import hashlib
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    pin_code = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # eKYC or face scan verified
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ], blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # Resolve reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="custom_user_set",  # 👈 This avoids clash
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",  # 👈 This avoids clash
        related_query_name="user",
    )

    def __str__(self):
        return self.email or self.username


class NotificationSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey('website.Event', on_delete=models.CASCADE)
    paid_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.phone} - {self.event.name}"


class UserSession(models.Model):
    """
    Server-side representation of a single browser/device session.
    Anonymous visitors are tied to a stable visitor_id cookie so we can stitch
    sessions even when they are not authenticated.
    """

    class DeviceType(models.TextChoices):
        DESKTOP = "desktop", "Desktop"
        TABLET = "tablet", "Tablet"
        MOBILE = "mobile", "Mobile"
        BOT = "bot", "Bot / Crawler"
        UNKNOWN = "unknown", "Unknown"

    session_id = models.CharField(max_length=255, unique=True)
    visitor_id = models.CharField(max_length=64, db_index=True, default=uuid.uuid4)
    session_fingerprint = models.CharField(max_length=128, blank=True, db_index=True)
    user_agent_hash = models.CharField(max_length=64, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_authenticated = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    client_language = models.CharField(max_length=32, blank=True)
    client_timezone = models.CharField(max_length=64, blank=True)
    device_type = models.CharField(
        max_length=20, choices=DeviceType.choices, default=DeviceType.UNKNOWN
    )
    device_family = models.CharField(max_length=120, blank=True)
    os = models.CharField(max_length=120, blank=True)
    browser = models.CharField(max_length=120, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)
    app_version = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=120, blank=True)
    region = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    isp = models.CharField(max_length=255, blank=True)
    referrer = models.TextField(blank=True)
    entry_url = models.TextField(blank=True)
    exit_url = models.TextField(blank=True)
    landing_page_title = models.CharField(max_length=255, blank=True)
    utm_source = models.CharField(max_length=120, blank=True)
    utm_medium = models.CharField(max_length=120, blank=True)
    utm_campaign = models.CharField(max_length=120, blank=True)
    utm_term = models.CharField(max_length=120, blank=True)
    is_bot = models.BooleanField(default=False)
    bot_score = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["visitor_id", "started_at"]),
            models.Index(fields=["is_authenticated"]),
        ]

    def __str__(self):
        label = (
            self.user.email
            if self.user
            else f"Anon ({self.country or 'Unknown'} - {self.ip_address})"
        )
        return f"{label} - {self.session_id}"

    def mark_ended(self):
        self.ended_at = timezone.now()
        self.save(update_fields=["ended_at"])

    @staticmethod
    def build_fingerprint(visitor_id: str, user_agent: str, ip_address: str) -> str:
        """
        Create a reproducible fingerprint to link related sessions together.
        """
        raw = f"{visitor_id}:{user_agent}:{ip_address}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def attach_user(self, user):
        """
        Associate the session with an authenticated user.
        """
        if user and (self.user_id != user.id or not self.is_authenticated):
            self.user = user
            self.is_authenticated = True
            self.save(update_fields=["user", "is_authenticated"])

    @property
    def duration_seconds(self):
        end = self.ended_at or timezone.now()
        return int((end - self.started_at).total_seconds())


class UserActivity(models.Model):
    """
    Fine grained request + custom event history that is linked to a session.
    """

    class EventType(models.TextChoices):
        PAGE_VIEW = "page_view", "Page view"
        API_REQUEST = "api_request", "API Request"
        INTERACTION = "interaction", "UI Interaction"
        AUTH = "auth", "Authentication"
        CUSTOM = "custom_event", "Custom Event"

    session = models.ForeignKey(
        UserSession, on_delete=models.CASCADE, related_name="activities"
    )
    event_type = models.CharField(
        max_length=50, choices=EventType.choices, default=EventType.PAGE_VIEW
    )
    url = models.TextField()
    path = models.TextField()
    view_name = models.CharField(max_length=255, blank=True)
    handler = models.CharField(max_length=255, blank=True)
    method = models.CharField(max_length=10, blank=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    country = models.CharField(max_length=120, blank=True)
    referrer = models.TextField(blank=True)
    query_params = models.JSONField(default=dict, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["event_type"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["response_time_ms"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.path}"

    @staticmethod
    def sanitize_payload(data):
        """
        Ensure payload stored is JSON serializable.
        """
        if data is None:
            return {}
        if isinstance(data, (dict, list)):
            return data
        text_value = str(data)
        if len(text_value) > 2000:
            text_value = text_value[:2000] + "...[truncated]"
        return {"value": text_value}