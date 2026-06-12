import re

from django import template

register = template.Library()


@register.filter
def formato_tel(value):
    digits = re.sub(r'\D', '', str(value or ''))
    if len(digits) == 11:
        return f'({digits[:2]}) {digits[2:7]}-{digits[7:]}'
    if len(digits) == 10:
        return f'({digits[:2]}) {digits[2:6]}-{digits[6:]}'
    return value
