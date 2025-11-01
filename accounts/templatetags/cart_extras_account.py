from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Safely gets a value from a dictionary in templates."""
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return None
