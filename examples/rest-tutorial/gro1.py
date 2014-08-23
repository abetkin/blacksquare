
from groutines import FCall, Event, switch
from dec import groutine

@groutine.wrapper()
#FCall('rest_framework.views.APIView.dispatch',
#                        argnames=['request']
#                        )
#                  typ='ENTER'
#                  )
def dispatch(#view, req, **kw
             ):
    value = FCall('rest_framework.views.APIView.dispatch').wait()
    view, req = value
#    import ipdb; ipdb.set_trace()
    Event('DISPATCH').fire(view, None)
    Event('RESP').fire(value.rv.data)
    

@groutine.wrapper(Event('RESP'))
def respons(resp):
    print (resp)
    
@groutine.wrapper(Event('DISPATCH'))
def print_view(view, req):
    print (req.__class__, view)
