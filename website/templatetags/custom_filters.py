from django import template

register = template.Library()

@register.filter
def replace(value, args):
    """
    Replaces characters in a string.
    Usage: {{ value|replace:"_: " }} -> replaces "_" with " "
    """
    if args and ":" in args:
        old, new = args.split(":")
        return value.replace(old, new)
    return value

@register.filter
def intdiv(value, arg):
    """
    Integer division.
    """
    try:
        return int(value) // int(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mod(value, arg):
    """
    Modulus operator.
    """
    try:
        return int(value) % int(arg)
    except (ValueError, ZeroDivisionError):
        return 0
