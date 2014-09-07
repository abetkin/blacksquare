# -*- coding: utf-8 -*-

from .. import InteractiveScenario


class GMiddleware(object):

    def __init__(self):
        pass
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        #import ipdb
        #with ipdb.launch_ipdb_on_exception():

        s = InteractiveScenario(view_func, (request,))

        if self.get_options().get('shell_on_start'):
            import IPython
            IPython.embed()

            try:
                return s.result
            except AttributeError:
                return s.wait()

        # Shell is shown after the scenario was executed
        result = s.wait()
        import IPython
        IPython.embed()

        return result


    def get_options(self):
        # A stub.
        # Options can be set in settings.py
        # and overwritten with request arguments
        return {
            'shell_on_start': False,
        }


