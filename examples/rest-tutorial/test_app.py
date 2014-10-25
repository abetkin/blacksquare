
import unittest
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'tutorial.settings'
import django
django.setup()


from rest_framework import serializers as rest_serializers, fields as rest_fields

from blacksquare.patching import Patch, patch
from blacksquare.patching.base import InsertionWrapper, HookWrapper, PatchSuite


class SerializerPatch(Patch):
    parent = rest_serializers.Serializer

    from_native = patch()


class WritableFieldPatch(Patch):

    log_prefix = 'field:'

    parent = rest_fields.WritableField #TODO tuple? many places to patch

    field_from_native = patch()
    from_native = patch()

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
