from rest_framework import generics

class View(generics.CreateAPIView):

    export_attrs = 'request', 'queryset'
    
    
    # scrict / no strict




#
# Object -> Event
#



import Serializer

class LinkMixin:
    
    emit_events = True
    
    def __new__(cls, *args, **kw):
        1
        # emit event


class Filter:

    _fields = ()
    
    def __init__(self):
        # self.context.request
        Serializer(__link__=self).deserialize()
    
    
    
'''
Begin     __new__ ?
Finish    result

1) with stop(MyApp):
    cli.get('url')
2) loggin g <-> events
n) debug toolvbar

patching?  No need


'''
    
    
    