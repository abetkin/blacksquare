
from groutines import FCall, Event
from dec import groutine

@groutine.wrapper(FCall('rest_framework.views.APIView.dispatch'),
#                  typ='ENTER'
                  )
def dispatch(view, request, **kw
             ):
#    view, request = FCall(
#            'rest_framework.views.APIView.dispatch').wait(typ='ENTER')
#    import ipdb; ipdb.set_trace()
    Event('DISPATCH').fire(view, request)
    Event('RESP').fire(kw['rv'].data)
    

@groutine.wrapper(Event('RESP'))
def response(resp):
    print resp['snippets']
    
@groutine.wrapper(Event('DISPATCH'))
def print_view(view, req):
    print req.__class__, view
