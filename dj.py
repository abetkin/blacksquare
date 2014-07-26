# -*- coding: utf-8 -*-

import rest_framework as rest
#from greenery import start_all

from django.conf import settings
from util import object_from_name

class MainG(object):
    
    registry = {} # view: greenlets
    
    def __init__(self, view, request):
        self.view = view
        self.request = request
        
    
    def discover(self):
        for klass in self.view.__class__.__mro__:
            for obj in getattr(klass, '__groutines__', ()):
                _, obj = object_from_name(obj)
                self.registry.setdefault(klass, set()).add(obj)
            for obj in self.registry.get(klass, ()):
                yield obj
    
    def run(self):
        1

def for_view(klass):
    def decor(f):
        GreeneryDiscoverer.registry.setdefault(klass, set()).add(f)
        return f
    return decor


class GreenView(rest.views.APIView):
    
    def initial(self, request, *args, **kwargs):
        super(GreenView, self).initial(request, *args, **kwargs)
        discoverer = GreeneryDiscoverer(self, request)
        start_all(discoverer.discover())
        