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

Calculator_add = Calculator.add

class WithError(Calculator, metaclass=patch):

    def error(self):
        return 0.1 * self.val

    def add(self, a, b):
        self.val = a + b
        return self.val + self.error()


def replace_add(self, a, b):
    return a - b


#class TestPatching(unittest.TestCase):
#
#    def run(self, result=None):
#


class TestGlobalPatches(unittest.TestCase):

    def setUp(self):

        self.assertEqual(Calculator.add, Calculator_add)

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

    def tearDown(self):
        self.assertEqual(Calculator.add, Calculator_add)

class TestManagersStack(unittest.TestCase):

    def setUp(self):
        self.assertEqual(Calculator.add, Calculator_add)
        print('start')

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

    def tearDown(self):
        print('end')
        self.assertEqual(Calculator.add, Calculator_add)

class TestFormat(unittest.TestCase):

    def setUp(self):
        self.assertEqual(Calculator.add, Calculator_add)
        logger = Logger.instance()
        while logger: logger.pop()

    def runTest(self):
        calc = Calculator()

        with Patches( Patch(Calculator, 'add', replace_add)):
            self.assertEqual( calc.add(2, 3), -1)

        out = str(Logger.instance())
        self.assertEqual(out, 'Call to add ( => replace_add)')

    def tearDown(self):
        self.assertEqual(Calculator.add, Calculator_add)


class TestEmbed(unittest.TestCase):

    def setUp(test):
        test.assertEqual(Calculator.add, Calculator_add)

        class SetBP(BaseConfig):

            def is_set_bp_for(self, wrapper):
                func = wrapper.wrapped
                return func is Calculator.add

            use_ipython = False

            def test_interactive(self, ctx):
                test.assert_( hasattr(ctx, '_tree'))

        SetBP()

    def runTest(self):
        calc = Calculator()


        with Patches( Patch(Calculator, 'add', replace_add)):
            self.assertEqual( calc.add(2, 3), -1)

    def tearDown(self):
        self.assertEqual(Calculator.add, Calculator_add)

