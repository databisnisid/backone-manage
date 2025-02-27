from django import template
import random

register = template.Library()


@register.simple_tag
def random_wallpaper():
    index = random.randint(1, 9)
    return f"/static/dashboard/wallpapers/wallpaper-{index}.jpg"
