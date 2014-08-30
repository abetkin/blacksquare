# -*- coding: utf-8 -*-

import os
from groutines import Groutine
import re
from util import object_from_name
from scenario import InteractiveScenario
from discovery import DefaultFinder
import django

class GMiddleware(object):

    def __init__(self):
        from django.conf import settings
        finder = getattr(settings, 'GROUTINES_FINDER', DefaultFinder())
        self._groutines = finder.discover() # dups?
        
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        self.groutines = []
        for func in self._groutines:
            gr = Groutine(func)
            self.groutines.append(gr)
            gr.switch()
        
        s = InteractiveScenario(view_func, (request,))
        import IPython
        IPython.embed()
        # TODO: kill shell when scenario ends
        #       use response from scenario
        return django.http.HttpResponse()
    
    def process_response(self, request, response):
        for gr in self.groutines:
            gr.throw()
        return response

