import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'tutorial.settings'
import django
django.setup()

from django.test import Client

#client = Client()
#resp = client.get('/users/')
#print resp.status_code

from django.contrib.auth.models import User

import SUCH

with SUCH.A('scenario check 200') as it:
    with it.wait_for('rest_framework.views.APIView.check_permissions') as it:
        @it.has_pre_hook()
        def _(case, *args, **kw):
            print args, kw
            case.forced_rv = True
    
        with it.wait_for('snippets.views.SnippetViewSet.pre_save') as it:
            @it.has_pre_hook()
            def _(case, obj, *args, **kw):
                case.forced_rv = None
    
            with it.wait_for('rest_framework.serializers.Serializer.is_valid') as it:
                @it.has_post_hook()
                def _(case, serializer, *args, **kw):
                    print serializer, args, kw
                    serializer.object.owner = User.objects.get(username='vitalii')
                    assert case.rv == True

            
            
    @it.should('create objects')
    def _(case):
        it.client = Client()
#        it.client.login(username='vitalii', password='root')
        data = {
            'title': 'Tree',
            'code': '''\
from collections import defaultdict

def tree():
    return defaultdict(tree)
''',
        }
        resp = it.client.post('/snippets/', data)
        resp.render()
        case.assertEqual(resp.status_code, 201)

#    with it.having('scenario: ') as it:
#        
    
it.createTests(globals())