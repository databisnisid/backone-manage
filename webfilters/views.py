from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from .models import WebFilters


def get_webfilter(request, uuid):
    print(uuid)
    try:
        webfilters = WebFilters.objects.get(uuid=uuid)
        alldomains = webfilters.domains
        #for filter in webfilters:
        #    alldomains += filter.domains
        #    alldomains += '\n'
    except ObjectDoesNotExist:
        alldomains = ''

    return HttpResponse(alldomains, content_type='text/plain')




