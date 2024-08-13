from os.path import basename
from django import template

register = template.Library()

@register.filter
def custom_basename(value):
    return basename(value)

register.filter('custom_basename', custom_basename)