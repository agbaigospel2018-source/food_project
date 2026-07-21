from django import template
from django.conf import settings

register = template.Library()


@register.filter
def currency(value):
    try:
        return f"{getattr(settings, 'MENU_CURRENCY_SYMBOL', '₦')}{value:,.2f}"
    except (TypeError, ValueError):
        return value
