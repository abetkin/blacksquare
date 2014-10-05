#!env python3
import unittest

from blacksquare.config import Config as BaseConfig
from blacksquare.patch import Patch, patch
from blacksquare.manage import Patches
from blacksquare.manage.handlers import ManagersStack, GlobalPatches

from blacksquare.util import import_obj

from blacksquare.patch.events import Logger

def make_patch(import_path, *args, **kw):
    parent, attr, _ = import_obj(import_path)
    return Patch(parent, attr, *args, **kw)



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

class TestGlobalPatches(unittest.TestCase):

    def setUp(self):
        class WithGlobalPatches(BaseConfig):
            def get_controller_class(self):
                return GlobalPatches

        WithGlobalPatches()


    def runTest(self):
        calc = Calculator()

        with Patches( Patch(Calculator, 'add', replace_add)) as m:
            self.assertEqual( calc.add(2, 3), -1)
            with Patches( *WithError()):
                self.assertAlmostEqual( calc.add(2, 3), 5.5)
            self.assertEqual( calc.add(2, 3), 5.5)
        self.assertEqual( calc.add(2, 3), 5)


class TestManagersStack(unittest.TestCase):

    def setUp(self):
        class WithManagersStack(BaseConfig):
            def get_controller_class(self):
                return ManagersStack

        WithManagersStack()

    def runTest(self):
        calc = Calculator()

        with Patches( Patch(Calculator, 'add', replace_add)) as m:
            self.assertEqual( calc.add(2, 3), -1)
            with Patches( *WithError()):
                self.assertAlmostEqual( calc.add(2, 3), 5.5)
            self.assertEqual( calc.add(2, 3), -1)
        self.assertEqual( calc.add(2, 3), 5)


class TestFormat(unittest.TestCase):

    def runTest(self):
        calc = Calculator()

        with Patches( Patch(Calculator, 'add', replace_add)):
            self.assertEqual(
                    calc.add(2, 3),
                    -1)
        out = str(Logger.instance())
        self.assertEqual(out, 'Call to add ( => replace_add)')
