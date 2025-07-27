"""Custom template tags and filters for dashboard app."""

from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    """Look up a key in a dictionary."""
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key, False)
    return False


@register.filter
def replace(value, arg):
    """Replace characters in a string."""
    if not value:
        return value
    old, new = arg.split(',', 1)
    return value.replace(old, new)


@register.filter
def format_permission_name(value):
    """Format permission key to readable name."""
    if not value:
        return value
    # Replace underscores with spaces and title case
    return value.replace('_', ' ').title()