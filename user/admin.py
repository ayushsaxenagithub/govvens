from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    NotificationSubscription,
    User,
    UserActivity,
    UserSession,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "username", "is_staff", "is_verified", "last_login")
    list_filter = ("is_staff", "is_superuser", "is_verified", "is_active")
    ordering = ("email",)
    search_fields = ("email", "username", "phone")
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone", "pin_code")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Verification", {"fields": ("is_verified", "date_of_birth", "gender")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


@admin.register(NotificationSubscription)
class NotificationSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "paid_fee", "notified", "created_at")
    list_filter = ("notified", "event")
    search_fields = ("user__email", "user__phone", "event__name")


class UserActivityInline(admin.TabularInline):
    model = UserActivity
    extra = 0
    readonly_fields = (
        "event_type",
        "path",
        "method",
        "status_code",
        "timestamp",
        "referrer",
    )
    can_delete = False
    show_change_link = True


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = (
        "session_id",
        "user",
        "visitor_id",
        "session_fingerprint",
        "ip_address",
        "country",
        "device_type",
        "browser",
        "started_at",
        "last_activity_at",
        "ended_at",
    )
    list_filter = (
        "device_type",
        "country",
        "is_authenticated",
        "started_at",
        "browser",
        "is_bot",
    )
    search_fields = (
        "session_id",
        "visitor_id",
        "session_fingerprint",
        "ip_address",
        "user__email",
    )
    readonly_fields = (
        "session_id",
        "visitor_id",
        "session_fingerprint",
        "user_agent_hash",
        "user",
        "is_authenticated",
        "ip_address",
        "user_agent",
        "client_language",
        "client_timezone",
        "device_type",
        "device_family",
        "os",
        "browser",
        "browser_version",
        "app_version",
        "country",
        "region",
        "city",
        "latitude",
        "longitude",
        "isp",
        "referrer",
        "entry_url",
        "exit_url",
        "landing_page_title",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "is_bot",
        "bot_score",
        "metadata",
        "started_at",
        "last_activity_at",
        "ended_at",
    )
    date_hierarchy = "started_at"
    inlines = [UserActivityInline]


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "event_type",
        "path",
        "view_name",
        "method",
        "status_code",
        "response_time_ms",
        "timestamp",
    )
    list_filter = ("event_type", "status_code", "timestamp", "view_name")
    search_fields = (
        "path",
        "view_name",
        "session__session_id",
        "session__user__email",
    )
    readonly_fields = (
        "session",
        "event_type",
        "url",
        "path",
        "view_name",
        "handler",
        "method",
        "status_code",
        "response_time_ms",
        "client_ip",
        "user_agent",
        "country",
        "referrer",
        "query_params",
        "payload",
        "metadata",
        "timestamp",
    )
