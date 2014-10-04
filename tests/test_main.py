#!env python3
import unittest

from blacksquare.config import Config
from blacksquare.patch import Patch, patch
from blacksquare.manager import Patches

from blacksquare.util import import_obj

def make_patch(import_path, *args, **kw):
    parent, attr, _ = import_obj(import_path)
    return Patch(parent, attr, *args, **kw)


#class MyConfig(Config):
#
#    def get_patches(self):
#        return [
#
#        ]

class Calculator:

    def __init__(self):
        self.val = 0

    def add(self, a, b):
        return a + b


class WithError(Calculator, metaclass=patch):

    def error(self):
        return 0.1 * self.val

    def add(self, a, b):
        self.val = a + b
        return self.val + self.error()

def replace_add(self, a, b):
    return a - b

class Test(unittest.TestCase):
    def setUp(self):
        global calc
        calc = Calculator()

    def runTest(self):
        with Patches( Patch(Calculator, 'add', replace_add)) as m:
            self.assertEqual( calc.add(2, 3), -1)
            with Patches( *WithError()):
                self.assertAlmostEqual( calc.add(2, 3), 5.5)
            self.assertEqual( calc.add(2, 3), -1)
        self.assertEqual( calc.add(2, 3), 5)
