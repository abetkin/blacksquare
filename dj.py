# -*- coding: utf-8 -*-

import rest_framework as rest
import greenlet

from django.conf import settings
from util import object_from_name

class MainG(object):
    #XXX: cannot switch to another thread
    
    registry = {} # {view: greenlet functions}
    
    def __init__(self, view, request):
        self.view = view
        self.request = request
        
    
    def discover(self):
        for mod in getattr(settings, 'GROUTINES_MODULES', []):
            __import__(mod)
        
        for klass in self.view.__class__.__mro__:
            for obj in getattr(klass, '__groutines__', ()):
                _, obj = object_from_name(obj)
                self.registry.setdefault(klass, set()).add(obj)
            return self.registry.get(klass, ())
    
    def run(self):
        greenlet_functions = self.discover()
        greenlets = [greenlet.greenlet(f) for f in greenlet_functions]
        for gr in greenlets:
            gr.switch()


def for_view(klass):
    def decor(f):
        MainG.registry.setdefault(klass, set()).add(f)
        return f
    return decor


class GreenView(rest.views.APIView):
    
    def initial(self, request, *args, **kwargs):
        MainG(self, request).run()
        super(GreenView, self).initial(request, *args, **kwargs)
        
        