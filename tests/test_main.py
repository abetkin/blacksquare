#!env python3
import unittest
import random
import logging

from blacksquare.config import Config as BaseConfig
from blacksquare.patch import Patch, patch
from blacksquare.manage import Patches
from blacksquare.manage.handlers import ManagersStack, GlobalPatches
from blacksquare.manage.events import PatchesEnter, PatchesExit
from blacksquare.manage.context import ContextTree
from blacksquare.util import import_obj

from blacksquare.core.events import Logger

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
                test.assertEqual(ctx['my.var'], 'my.value')

        SetBP()

    def runTest(self):
        ContextTree.instance()['my.var'] = 'my.value'
        calc = Calculator()

        with Patches( Patch(Calculator, 'add', replace_add)):
            self.assertEqual( calc.add(2, 3), -1)

    def tearDown(self):
        self.assertEqual(Calculator.add, Calculator_add)


class HackUnittest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        class SetController(BaseConfig):
            def get_controller_class(self):
                return random.choice( (ManagersStack, GlobalPatches))

        SetController()

        cls.unittest_TestCase_run = unittest.TestCase.run

        def runfunc(test, result=None):
            ContextTree.instance()['testing.test'] = test._testMethodName
            unittest.TestCase.run(test, result)

        cls._hacks = Patches( Patch(unittest.TestCase, 'run', runfunc))
        PatchesEnter.handle(cls._hacks.patches, cls._hacks)


    def test_with_name(self):
        calc = Calculator()

        with Patches( Patch(Calculator, 'add', replace_add)):
            self.assertEqual( calc.add(2, 3), -1)
            self.assertEqual(ContextTree.instance()['testing.test'],
                             'test_with_name')
        self.assertEqual(ContextTree.instance()['testing.test'],
                             'test_with_name')


    @classmethod
    def tearDownClass(cls):
        PatchesExit.handle(cls._hacks)
        assert unittest.TestCase.run == cls.unittest_TestCase_run
