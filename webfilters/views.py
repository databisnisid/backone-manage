from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from .models import WebFilters, WebFiltersMembers
from networks.models import Networks


'''
def get_webfilter(request, uuid):
    print('Get WebFilters base on uuid:', uuid)
    try:
        webfilters = WebFilters.objects.get(uuid=uuid)
        alldomains = webfilters.domains
        #for filter in webfilters:
        #    alldomains += filter.domains
        #    alldomains += '\n'
    except ObjectDoesNotExist:
        alldomains = ''

    return HttpResponse(alldomains, content_type='text/plain')


def get_webfilter_white(request, uuid):
    print('Get WebFilters White base on uuid:', uuid)
    try:
        webfilters = WebFilters.objects.get(uuid=uuid)
        alldomains = webfilters.domains_white
        #for filter in webfilters:
        #    alldomains += filter.domains
        #    alldomains += '\n'
    except ObjectDoesNotExist:
        alldomains = ''

    return HttpResponse(alldomains, content_type='text/plain')


def get_webfilter_block(request, uuid):
    print('Get WebFilters Block base on uuid:', uuid)
    try:
        webfilters = WebFilters.objects.get(uuid=uuid)
        #alldomains = webfilters.is_default_block
        alldomains = '1' if webfilters.is_default_block else '0'
        #for filter in webfilters:
        #    alldomains += filter.domains
        #    alldomains += '\n'
    except ObjectDoesNotExist:
        alldomains = '0'

    return HttpResponse(alldomains, content_type='text/plain')

def network_webfilter_block(request, network):
    print('Get WebFilters Block base on network_id:', network)
    try:
        webfilters = WebFilters.objects.get(uuid=uuid)
        #alldomains = webfilters.is_default_block
        alldomains = '1' if webfilters.is_default_block else '0'
        #for filter in webfilters:
        #    alldomains += filter.domains
        #    alldomains += '\n'
    except ObjectDoesNotExist:
        alldomains = '0'

    return HttpResponse(alldomains, content_type='text/plain')

'''

def get_webfilter_by_member(request, member):
    print('(return empty) Get WebFilters base on member: ', member)
    '''
    try:
        result = WebFiltersMembers.objects.get(member__member_id=member)
        #webfilters = WebFilters.objects.get(webfilter=result.webfilter)
        alldomains = result.webfilter.domains
    except ObjectDoesNotExist:
        alldomains = ''
    '''
    alldomains = ''

    return HttpResponse(alldomains, content_type='text/plain')


def get_webfilter_by_network(request, network_id):
    print('Get WebFilters base on NetworkID: ', network_id)
    try:
        network = Networks.objects.get(network_id=network_id)

        try:
            webfilters = WebFilters.objects.get(network=network)
            alldomains = '1\n' if webfilters.is_default_block else '0\n'
            alldomains += webfilters.domains_white if webfilters.is_default_block else webfilters.domains

        except ObjectDoesNotExist:
            alldomains = ''

    except ObjectDoesNotExist:
        alldomains = ''


    return HttpResponse(alldomains, content_type='text/plain')

