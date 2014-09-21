
import unittest
import os

from blacksquare import Patch, PatchManager


import django


os.environ['DJANGO_SETTINGS_MODULE'] = 'tutorial.settings'
django.setup()
from snippets.models import Snippet
from django.db import models

#def patch(cls):
#    '''
#    creating patch at import time.
#    '''
#    patch = Patch.from_classdef(cls)
#    PatchManager.instance().records_no_deps.append(patch)
#    return cls



class Some(unittest.TestCase):
    1

#@patch
class ReplaceModel(models.Model, metaclass=patch):
    def save(self, **kw):
        if not isinstance(self, Snippet):
            return super().save(self, **kw)
        print('No save!')
        print('tried to save %s into %s' % (kw, self))


#class ReplaceModel:
#    def save(old, self, **kw):
#        if not isinstance(self, Snippet):
#            return old(self, **kw)
#        print('No save!')
#        print('tried to save %s into %s' % (kw, self))

if __name__ == '__main__':


    patches = [
        Patch('rest_framework.views.APIView.dispatch'),
        Patch('django.db.models.Model.save', ReplaceModel.save),
    ]

    pm = PatchManager(*patches)

    def do():
        from rest_framework.test import APIClient
        cl = APIClient()
        cl.login(username='vitalii', password='123')
        resp = cl.post('/snippets/', {'title': 'titlu', 'code': 'codu'})
        print (resp.data)

    with pm:
        do()
