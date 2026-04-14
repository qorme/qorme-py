from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag
def address(address_obj):
    return render_to_string("test_app/includes/address.html", {"address": address_obj})
