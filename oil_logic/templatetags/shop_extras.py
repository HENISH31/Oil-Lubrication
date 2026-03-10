from django import template

register = template.Library()

@register.filter(name='is_in')
def is_in(value, list_obj):
    if not list_obj:
        return False
    if isinstance(list_obj, str):
        list_obj = [x.strip() for x in list_obj.split(',')]
    return value in list_obj

@register.filter(name='is_eq')
def is_eq(value, arg):
    return str(value) == str(arg)

@register.filter(name='is_in_attr')
def is_in_attr(value, list_obj):
    if not list_obj:
        return ""
    if isinstance(list_obj, str):
        list_obj = [x.strip() for x in list_obj.split(',')]
    return "checked" if value in list_obj else ""

@register.filter(name='is_eq_attr')
def is_eq_attr(value, arg):
    return "selected" if str(value) == str(arg) else ""

@register.filter(name='is_ge')
def is_ge(value, arg):
    try:
        return float(value) >= float(arg)
    except (ValueError, TypeError):
        return False

@register.filter(name='is_gt')
def is_gt(value, arg):
    try:
        return float(value) > float(arg)
    except (ValueError, TypeError):
        return False
