# -*- coding: utf-8 -*-

import os
from groutines import Groutine
import re
from util import object_from_name


class GMiddleware(object):
    
    def find_groutines(self):
        from django.conf import settings
        regexp = settings.GROUTINES_FINDER_REGEXP
        for path, dirs, files in os.walk(settings.BASE_DIR):
            for fname in files:
                if not re.match(r'\w+\.py$', fname) or not re.match(regexp, fname):
                    continue
                parts = os.path.relpath(path, settings.BASE_DIR
                                ).split(os.path.sep)
                # probably exists a more elegant solution for import
                obj_path = '.'.join(parts + [fname[:-3]]) 
                _, _, mod = object_from_name(obj_path)
                for attr in dir(mod):
                    if isinstance(getattr(mod, attr), Groutine):
                        yield getattr(mod, attr)
    
    def __init__(self):
        self.groutines = list(self.find_groutines())
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        for gr in self.groutines:
            gr.start()
    
    def process_response(self, request, response):
        for gr in tuple(self.groutines):
            gr.greenlet.throw() # killing it
            self.groutines.remove(gr)
        return response

