# -*- coding: utf-8 -*-

from groutines import make_groutine, FunctionCall, Event, switch, greenlet
from dec import groutine
import IPython, ipdb

class GMiddleware(object):
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        for func in [start_view, f, f1]:
            make_groutine(func)

@groutine()
def start_view():
    view, request = FunctionCall(
            'rest_framework.views.APIView.dispatch').wait()[:2]
    Event(1).fire(view, request)

@groutine(1)
def f(view, request):
    print view.__class__.__name__
    
@groutine(1)
def f1(view, request):
    print request.path