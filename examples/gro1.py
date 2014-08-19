
from groutines import FCall, Event
from dec import groutine

@groutine.wrapper()
def dispatch():
    view, request = FCall(
            'rest_framework.views.APIView.dispatch').wait(typ='ENTER')
    Event('DISPATCH').fire(view, request)
    

@groutine.wrapper(Event('DISPATCH'))
def print_view(req, view):
    print req.__class__, view