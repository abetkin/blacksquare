
import unittest
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'tutorial.settings'
import django
django.setup()


from rest_framework import serializers as rest_serializers, fields as rest_fields

from blacksquare.patching import Patch, patch
from blacksquare.patching.base import InsertionWrapper, HookWrapper, PatchSuite
from blacksquare.patching.events import HookFunctionExecuted
from blacksquare.util import ContextAttribute

from IPython.lib.pretty import pretty


class SerializerPatch(Patch):
    parent = rest_serializers.Serializer

    from_native = patch()

class FieldFromNativeEvent(HookFunctionExecuted):

    log_prefix = None


    def _log_pretty_(self, p, cycle): # remove _
        if cycle:
            p.text('HookFunction(..)')
            return
        with p.group(len(self.log_prefix), self.log_prefix):
            p.text( pretty(self.field_value))
            p.text(' was set into ')
            p.breakable()
            p.text(self.field_name)


class WritableFieldPatch(Patch):

    parent = rest_fields.WritableField #TODO tuple? if many places to patch

    from_native = patch()

    @patch(wrapper_type=HookWrapper, pass_event=True, event_class=FieldFromNativeEvent)
    def field_from_native(self, data, files, field_name, into,
                          return_value, event):
        #import ipdb; ipdb.set_trace()

        event.published_context = ('log_prefix',)
        event.__dict__.update({
            'log_prefix': '-> ',
            'field_value': into.get(field_name),
            'field_name': field_name,
        })

if __name__ == '__main__':


    def do():
        from rest_framework.test import APIClient
        cl = APIClient()
        cl.login(username='vitalii', password='123')
        resp = cl.post('/snippets/', {'title': 'titlu', 'code': 'codu'})
        print (resp.data)

    import ipdb
    with ipdb.launch_ipdb_on_exception():
        with (SerializerPatch.make_patches()
              + WritableFieldPatch.make_patches()):
            do()
