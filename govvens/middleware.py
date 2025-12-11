"""
Project level middleware utilities with bot detection and security enhancements.
"""
from __future__ import annotations

import time
import logging
import re

from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from django.http import HttpResponse
from django.core.cache import cache
import requests

from user.models import UserActivity, UserSession
from user.services.tracking import (
    detect_device,
    extract_utm,
    get_client_ip,
    get_or_create_visitor_id,
    lookup_geo_data,
    parse_json_body,
)

logger = logging.getLogger(__name__)


class AdminProtectionMiddleware:
    """
    Middleware to protect /admin routes - only allows logged-in staff users
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request is for admin
        if request.path.startswith("/admin/"):
            # Allow access to admin login and logout pages
            if request.path in ["/admin/login/", "/admin/logout/"]:
                response = self.get_response(request)
                return response

            # For all other admin pages, check if user is authenticated and is staff
            if not request.user.is_authenticated or not request.user.is_staff:
                return redirect("landing_page")

        response = self.get_response(request)
        return response


class UserTrackingMiddleware:
    """
    Persist request level telemetry to the database for every visitor.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.ignored_prefixes = getattr(
            settings,
            "TRACKING_IGNORED_PATH_PREFIXES",
            ["/static/", "/media/"],
        )

    def __call__(self, request):
        if self._should_ignore(request.path):
            return self.get_response(request)

        start = time.perf_counter()
        visitor_id, require_cookie = get_or_create_visitor_id(request)
        request.tracking_visitor_id = visitor_id
        session_record = self._prepare_session(request, visitor_id)
        request.tracking_session = session_record

        response = self.get_response(request)

        duration_ms = int((time.perf_counter() - start) * 1000)
        self._log_activity(request, response, session_record, duration_ms)
        self._update_session_exit(request, session_record)

        if require_cookie:
            response.set_cookie(
                getattr(
                    settings, "TRACKING_VISITOR_COOKIE_NAME", "gov_visitor_id"
                ),
                visitor_id,
                max_age=getattr(
                    settings, "TRACKING_VISITOR_COOKIE_AGE", 31536000
                ),
                secure=not settings.DEBUG,
                httponly=False,
                samesite="Lax",
            )

        return response

    def _should_ignore(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.ignored_prefixes)

    def _prepare_session(self, request, visitor_id: str) -> UserSession:
        if not request.session.session_key:
            request.session.create()

        session_id = request.session.session_key
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        language = (
            request.META.get("HTTP_ACCEPT_LANGUAGE", "").split(",")[0].strip()
        )
        timezone_hint = request.META.get("HTTP_X_TIMEZONE", "")
        device_info = detect_device(user_agent)
        utm_values = extract_utm(request)

        defaults = {
            "visitor_id": visitor_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "client_language": language,
            "client_timezone": timezone_hint,
            "device_type": device_info["device_type"],
            "browser": device_info["browser"],
            "browser_version": device_info["browser_version"],
            "os": device_info["os"],
            "is_bot": device_info["is_bot"],
            "entry_url": request.build_absolute_uri(),
            "referrer": request.META.get("HTTP_REFERER", ""),
            "session_fingerprint": UserSession.build_fingerprint(
                visitor_id, user_agent, ip_address or ""
            ),
            "user_agent_hash": UserSession.build_fingerprint(
                "", user_agent, ""
            ),
            **utm_values,
        }

        session, created = UserSession.objects.get_or_create(
            session_id=session_id,
            defaults=defaults,
        )

        fields_to_update: list[str] = []

        if not created:
            for field, value in defaults.items():
                if value and getattr(session, field) != value:
                    setattr(session, field, value)
                    fields_to_update.append(field)
            if not session.entry_url:
                session.entry_url = request.build_absolute_uri()
                fields_to_update.append("entry_url")
            session.exit_url = request.build_absolute_uri()
            fields_to_update.append("exit_url")
        else:
            fields_to_update.append("exit_url")

        # Geo lookup is done once per session unless we do not yet know the country.
        if not session.country and ip_address:
            geo = lookup_geo_data(ip_address)
            if geo:
                from decimal import Decimal
                for field, value in geo.items():
                    if value is not None and value != "":
                        # Convert float to Decimal for latitude/longitude
                        if field in ('latitude', 'longitude') and isinstance(value, (int, float)):
                            try:
                                setattr(session, field, Decimal(str(value)))
                                fields_to_update.append(field)
                            except (ValueError, TypeError):
                                pass  # Skip invalid lat/lon values
                        elif field in ('country', 'region', 'city', 'isp'):
                            # Only update string fields if they have meaningful content
                            if value and str(value).strip():
                                setattr(session, field, str(value).strip())
                                fields_to_update.append(field)
                        else:
                            setattr(session, field, value)
                            fields_to_update.append(field)

        if request.user.is_authenticated:
            session.user = request.user
            session.is_authenticated = True
            fields_to_update.extend(["user", "is_authenticated"])

        if fields_to_update:
            session.save(update_fields=list(set(fields_to_update)))

        return session

    def _log_activity(
        self, request, response, session: UserSession, duration_ms: int
    ):
        try:
            resolver_match = getattr(request, "resolver_match", None)
            view_name = resolver_match.view_name if resolver_match else ""
            handler = (
                f"{resolver_match.func.__module__}.{resolver_match.func.__name__}"
                if resolver_match
                else ""
            )
            event_type = self._resolve_event_type(request)

            query_params = {
                key: values if len(values) > 1 else values[0]
                for key, values in request.GET.lists()
            }

            payload = {}
            if request.method in {"POST", "PUT", "PATCH"}:
                if request.content_type == "application/json":
                    payload = parse_json_body(request)
                else:
                    payload = dict(request.POST.items())

            UserActivity.objects.create(
                session=session,
                event_type=event_type,
                url=request.build_absolute_uri(),
                path=request.path,
                view_name=view_name,
                handler=handler,
                method=request.method,
                status_code=getattr(response, "status_code", None),
                response_time_ms=duration_ms,
                client_ip=session.ip_address,
                user_agent=session.user_agent,
                country=session.country,
                referrer=request.META.get("HTTP_REFERER", ""),
                query_params=query_params,
                payload=UserActivity.sanitize_payload(payload),
                metadata={
                    "user_id": request.user.id if request.user.is_authenticated else None,
                    "is_secure": request.is_secure(),
                    "is_ajax": request.headers.get("X-Requested-With") == "XMLHttpRequest",
                    "timestamp": timezone.now().isoformat(),
                },
            )
        except Exception:  # pragma: no cover - telemetry failures should not block requests
            # Swallow errors to avoid interrupting user flow.
            pass

    def _resolve_event_type(self, request) -> str:
        if request.path.startswith("/api/"):
            return UserActivity.EventType.API_REQUEST
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            return UserActivity.EventType.INTERACTION
        if request.path.startswith("/user/") and request.method == "POST":
            return UserActivity.EventType.AUTH
        return UserActivity.EventType.PAGE_VIEW

    def _update_session_exit(self, request, session: UserSession):
        try:
            current_url = request.build_absolute_uri()
            if session.exit_url != current_url:
                session.exit_url = current_url
                session.save(update_fields=["exit_url"])
        except Exception:  # pragma: no cover
            pass


class BotDetectionMiddleware:
    """
    Middleware to detect and limit bot/crawler access
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.bot_user_agents = getattr(settings, 'BOT_USER_AGENTS', [])
        self.suspicious_patterns = getattr(settings, 'SUSPICIOUS_PATTERNS', [])
        self.bot_detection_enabled = getattr(settings, 'BOT_DETECTION_ENABLED', True)
    
    def __call__(self, request):
        if not self.bot_detection_enabled:
            return self.get_response(request)
        
        # Check for bot signatures
        if self._is_bot(request):
            ip_address = get_client_ip(request)
            logger.warning(f"Bot detected from IP: {ip_address}, User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
            
            # Mark the session as a bot
            if hasattr(request, 'tracking_session'):
                request.tracking_session.is_bot = True
                request.tracking_session.save(update_fields=['is_bot'])
        
        # Check for suspicious patterns (SQL injection, path traversal, etc)
        if self._has_suspicious_patterns(request):
            logger.warning(f"Suspicious pattern detected from {get_client_ip(request)}: {request.path}")
            # Still process the request but log it
        
        response = self.get_response(request)
        return response
    
    def _is_bot(self, request) -> bool:
        """Check if request is from a bot/crawler"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Check against known bot patterns
        for bot_pattern in self.bot_user_agents:
            if bot_pattern.lower() in user_agent:
                return True
        
        # Check for missing or empty user agent
        if not user_agent or user_agent.strip() == '':
            return True
        
        # Check for suspicious tools
        suspicious_tools = ['curl', 'wget', 'python', 'perl', 'java', 'ruby', 'scrapy']
        for tool in suspicious_tools:
            if tool in user_agent:
                return True
        
        return False
    
    def _has_suspicious_patterns(self, request) -> bool:
        """Check for SQL injection, XSS, path traversal, etc"""
        path = request.path.lower()
        query_string = request.get_full_path().lower()
        
        for pattern in self.suspicious_patterns:
            if pattern.lower() in path or pattern.lower() in query_string:
                return True
        
        # Check for path traversal attempts
        if '../' in path or '..\\' in path:
            return True
        
        return False


class RateLimitMiddleware:
    """
    Simple rate limiting middleware based on IP address
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_per_ip = getattr(settings, 'RATE_LIMIT_PER_IP', 500)
        self.rate_limit_window = 3600  # 1 hour
    
    def __call__(self, request):
        ip_address = get_client_ip(request)
        cache_key = f'rate_limit_{ip_address}'
        
        # Get current request count
        request_count = cache.get(cache_key, 0)
        
        # Check if exceeded limit
        if request_count >= self.rate_limit_per_ip:
            logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            return HttpResponse(
                'Rate limit exceeded. Please try again later.',
                status=429
            )
        
        # Increment counter
        cache.set(cache_key, request_count + 1, self.rate_limit_window)
        
        response = self.get_response(request)
        return response