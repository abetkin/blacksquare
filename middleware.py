# -*- coding: utf-8 -*-

from groutines import make_groutine, FunctionCall, Event, switch, greenlet
from dec import groutine
import IPython, ipdb

# TODO: `parent can't be on different thread`

class GMiddleware(object):
    
    @property
    def functions(self):
        return [
            start_view, _1,
        ]
    
    def __init__(self):
        self.groutines = set()
    
    def process_view(self, request, view_func, view_args, view_kwargs):
#        ipdb.set_trace()
        for func in self.functions:
            gr = make_groutine(func)
            self.groutines.add(gr)
        
    
    def process_response(self, request, response):
#        ipdb.set_trace()
        for gr in tuple(self.groutines):
            gr.throw()
            self.groutines.remove(gr)
            
        return response

@groutine()
def start_view():
    view, request = FunctionCall(
            'rest_framework.views.APIView.dispatch').wait()[:2]
    Event('DISPATCH').fire(view, request)

@groutine('DISPATCH')
def deserialization(view, request):
    srlzer, data, files = FunctionCall('rest_framework.serializers.Serializer'
                                       '.from_native').wait()
    print srlzer.get_fields()
    
    ('rest_framework.fields.Field.initialize').wait
    
    self, data, files, field_name, into = FunctionCall(
            'rest_framework.serializers.Serializer.field_from_native')


@groutine(FunctionCall('rest_framework.fields.Field.initialize'),
          once=False)
def _1(field_name, field, *args, **kw):
    print field_name

#@groutine('DESER_FIELD', once=False)
#def deserialize_field(field_name, data, into):
#    event = FunctionCall('rest_framework.serializers.Serializer.field_from_native')
#    event.wait('ENTER')
#    event.wait('EXIT')
    
#@groutine(1)
#def f1(view, request):
#    print request.path

