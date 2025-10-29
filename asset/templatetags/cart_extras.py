from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplies two numbers (for example: price * quantity)."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
