#!env python3
import unittest
import random
import logging

from blacksquare.config import Config as BaseConfig
from blacksquare.core.events import Event
from blacksquare.patch import Patch, patch, SimpleConditionalPatch
from blacksquare.manage import Patches
from blacksquare.manage.handlers import ManagersStack, GlobalPatches
from blacksquare.manage.events import PatchesEnter, PatchesExit
from blacksquare import get_config, get_context
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

class Config(BaseConfig):
    def get_controller_class(self):
        return random.choice( (ManagersStack, GlobalPatches))

Config()


class TestGlobalPatches(unittest.TestCase):

    def setUp(self):
        self.assertEqual(Calculator.add, Calculator_add)

        class WithGlobalPatches(Config):
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

        class WithManagersStack(Config):
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

        class SetBP(Config):

            def is_set_bp_for(self, wrapper):
                func = wrapper.wrapped
                return func is Calculator.add

            use_ipython = False

            def test_interactive(self, ctx):
                test.assertEqual(ctx['my.var'], 'my.value')

        SetBP()

    def runTest(self):
        get_context()['my.var'] = 'my.value'
        calc = Calculator()

        with Patches( Patch(Calculator, 'add', replace_add)):
            self.assertEqual( calc.add(2, 3), -1)

    def tearDown(self):
        self.assertEqual(Calculator.add, Calculator_add)


class HackUnittest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.unittest_TestCase_run = unittest.TestCase.run

        def runfunc(test, result=None):
            get_context()['testing.test'] = test._testMethodName
            unittest.TestCase.run(test, result)

        cls._hacks = Patches( Patch(unittest.TestCase, 'run', runfunc))
        PatchesEnter.handle(cls._hacks.patches, cls._hacks)


    def test_with_name(self):
        calc = Calculator()

        with Patches( Patch(Calculator, 'add', replace_add)):
            self.assertEqual( calc.add(2, 3), -1)
            self.assertEqual(get_context()['testing.test'],
                             'test_with_name')
        self.assertEqual(get_context()['testing.test'],
                             'test_with_name')


    @classmethod
    def tearDownClass(cls):
        PatchesExit.handle(cls._hacks)
        assert unittest.TestCase.run == cls.unittest_TestCase_run



class BadValue(Event):
    pass

class TestConditionalPatches(unittest.TestCase):

    class NumberGenerator:
        def generate_number(self):
            return random.randint(0, 1100)

    class PatchGenerator(NumberGenerator, metaclass=patch):
        def generate_number(self, return_value):
            if return_value > 1000:
                BadValue.emit(return_value)
            return random.randint(0, 10000)
        generate_number.is_hook = True

    class Printer:
        printed = []

        @classmethod
        def print(cls, value):
            #print(value, end=' ')
            cls.printed.append(value)

    class CondPatch(SimpleConditionalPatch):
        def __init__(self):
            super(TestConditionalPatches.CondPatch, self).__init__(
                TestConditionalPatches.Printer,
                'print',
                TestConditionalPatches.CondPatch.print_stub)

        event_to_listen = BadValue

        def print_stub(cls, value):
            #print(777, end=' ')
            TestConditionalPatches.Printer.printed.append(777)

    def setUp(self):
        self._patches = Patches( self.CondPatch(), *self.PatchGenerator())
        PatchesEnter.handle(self._patches.patches, self._patches)

    def runTest(self):
        printer = self.Printer()
        generator = self.NumberGenerator()
        for i in range(50):
            num = generator.generate_number()
            printer.print(num)

        for value in self.Printer.printed:
            self.assertLessEqual(value, 1000)

    def tearDown(self):
        PatchesExit.handle(self._patches)
