from django import template

register = template.Library()


@register.filter()
def cz_pluralize(value, suffixes):
    suffixes = suffixes.split(',')
    try:
        value = abs(value)
    except:
        value = 0

    if value == 0:
        return suffixes[2]
    if value == 1:
        return suffixes[0]
    if value < 5:
        return suffixes[1]
    return suffixes[2]
