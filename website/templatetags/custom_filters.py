from django import template

register = template.Library()

@register.filter
def replace(value, args):
    """
    Replace filter for Django templates
    Usage: {{ value|replace:"old:new" }}
    """
    if not args or ':' not in args:
        return value
    
    old, new = args.split(':', 1)
    return str(value).replace(old, new)

@register.filter
def format_event_type(value):
    """
    Format event type by replacing underscores with spaces and title-casing
    Usage: {{ event_type|format_event_type }}
    """
    return str(value).replace('_', ' ').title()
