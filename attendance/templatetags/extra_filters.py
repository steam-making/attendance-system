from django import template
register = template.Library()

@register.filter
def dict_get(d, key):
    if d is None:
        return None
    if isinstance(d, dict):
        return d.get(key)
    if isinstance(d, list):
        try:
            return d[int(key) % len(d)]
        except (ValueError, TypeError, ZeroDivisionError):
            return None
    return None

@register.filter
def split(value, delimiter):
    if value is None:
        return []
    return str(value).split(delimiter)

@register.filter
def startswith(value, arg):
    if value is None:
        return False
    return str(value).startswith(arg)

@register.filter
def contains(value, arg):
    if value is None:
        return False
    return arg in str(value)
