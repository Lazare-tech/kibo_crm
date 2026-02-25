# kibo_forms/templatetags/form_extras.py
from django import template
register = template.Library()

@register.filter
def dict_key(d, key):
    return d.get(key)



@register.filter
def percentage(count, total):
    try:
        # On évite la division par zéro et on calcule
        if total > 0:
            return round((float(count) / float(total)) * 100, 1)
        return 0
    except (ValueError, TypeError):
        return 0