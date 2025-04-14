from django import template
from django.template.defaultfilters import stringfilter
import json

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtrai o argumento do valor"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
    
@register.filter
def debug_value(value):
    """Retorna informações de debug sobre o valor"""
    if value is None:
        return "None (NoneType)"
    return f"{value} ({type(value).__name__})" 