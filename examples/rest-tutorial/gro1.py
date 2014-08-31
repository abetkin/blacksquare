
from groutines import Event, wait, groutine, loop
import collections

@groutine()
#FCall('rest_framework.views.APIView.dispatch',
#                        argnames=['request']
#                        )
#                  typ='ENTER'
#                  )
def dispatch(#view, req, **kw
             ):
    value = wait('rest_framework.views.APIView.dispatch')
    print( value )
    view, req, rv= value
    
    Event('DISPATCH')(view=view, request=req).fire()
    Event('RESP').fire(collections.OrderedDict(resp=rv.data))
    

@groutine('RESP')
def respons(resp):
    print (resp)
    
@loop('DISPATCH')
def print_view(view, request):
    print (request.__class__, view)

