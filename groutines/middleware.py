# -*- coding: utf-8 -*-

from . import Groutine, InteractiveScenario, DefaultFinder

class GMiddleware(object):

    def __init__(self):
        from django.conf import settings
        finder = getattr(settings, 'GROUTINES_FINDER', DefaultFinder())
        self._groutines = finder.discover() # dups?
        
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        import ipdb
        with ipdb.launch_ipdb_on_exception():
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
            import django
            return django.http.HttpResponse()
    
    def process_response(self, request, response):
        for gr in self.groutines:
            gr.throw()
        return response

