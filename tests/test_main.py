#!env python3
import unittest
import random
import logging

from blacksquare.config import Config as BaseConfig
from blacksquare.core.events import Event

from blacksquare.patch import Patch, patch, SimpleConditionalPatch
from blacksquare.patch.base import InsertionWrapper, HookWrapper
from blacksquare.manage import PatchSuite
from blacksquare.manage.handlers import PatchSuitesStack, GlobalPatches
from blacksquare.manage.events import PatchSuiteStart, PatchSuiteFinish
from blacksquare import get_config, get_context
from blacksquare.util import import_obj

from blacksquare.core.events import Logger

class Calculator:

    def add(self, a, b):
        return a + b

Calculator_add = Calculator.add

class BrokenCalculator(Patch):

    parent = Calculator

    @patch(wrapper_type=InsertionWrapper)
    def error(self):
        return 0.1 * self.val

    @patch()
    def add(self, a, b):
        self.val = a + b
        return self.val + self.error()

def replace_add(self, a, b):
    return a - b



class Config(BaseConfig):
    def get_controller_class(self):
        return random.choice( (PatchSuitesStack, GlobalPatches))

class TestCase(unittest.TestCase):
    def run(self, result=None):
        Config()
        super().run(result)


class Simplest(TestCase):

    def setUp(self):
        self.assertEqual(Calculator.add, Calculator_add)

    def runTest(self):
        calc = Calculator()

        with PatchSuite( Patch('add', replace_add, Calculator)):
            self.assertEqual( calc.add(2, 3), -1)


        self.assertEqual( calc.add(2, 3), 5)

    def tearDown(self):
        self.assertEqual(Calculator.add, Calculator_add)



class TestGlobalPatches(TestCase):

    def setUp(self):
        self.assertEqual(Calculator.add, Calculator_add)

        class WithGlobalPatches(Config):
            def get_controller_class(self):
                return GlobalPatches

        WithGlobalPatches()


    def runTest(self):
        calc = Calculator()

        with PatchSuite( Patch('add', replace_add, Calculator)):
            self.assertEqual( calc.add(2, 3), -1)
            with BrokenCalculator.make_patches():
                self.assertAlmostEqual( calc.add(2, 3), 5.5)
            self.assertEqual( calc.add(2, 3), 5.5)
        self.assertEqual( calc.add(2, 3), 5)

    def tearDown(self):
        self.assertEqual(Calculator.add, Calculator_add)


class TestPatchSuitesStack(TestCase):

    def setUp(self):
        self.assertEqual(Calculator.add, Calculator_add)

        class WithPatchSuitesStack(Config):
            def get_controller_class(self):
                return PatchSuitesStack

        WithPatchSuitesStack()

    def runTest(self):
        calc = Calculator()

        with PatchSuite( Patch('add', replace_add, Calculator)):
            self.assertEqual( calc.add(2, 3), -1)
            with BrokenCalculator.make_patches():
                self.assertAlmostEqual( calc.add(2, 3), 5.5)
            self.assertEqual( calc.add(2, 3), -1)

        self.assertEqual( calc.add(2, 3), 5)

    def tearDown(self):
        self.assertEqual(Calculator.add, Calculator_add)

class TestFormat(TestCase):

    def setUp(self):
        self.assertEqual(Calculator.add, Calculator_add)
        logger = Logger.instance()
        while logger: logger.pop()

    def runTest(self):
        calc = Calculator()

        with PatchSuite( Patch('add', replace_add, Calculator)):
            self.assertEqual( calc.add(2, 3), -1)

        out = str(Logger.instance())
        self.assertEqual(out, 'Call to add ( => replace_add)')

    def tearDown(self):
        self.assertEqual(Calculator.add, Calculator_add)


class TestEmbed(unittest.TestCase):

    def setUp(self):
        self.assertEqual(Calculator.add, Calculator_add)
        Logger()
        config = get_config()
        config.fake_interactive_shell = self._test_pdb
        config.set_breakpoint(0)

    def _test_pdb(self, _locals, _globals):
        ctx = _globals['get_context']()
        self.assertEqual(ctx['my.var'], 'my.value')
        self.assertEqual(_locals['ret'], -1)

    def runTest(self):
        get_context()['my.var'] = 'my.value'
        calc = Calculator()

        with PatchSuite( Patch('add', replace_add, Calculator)):
            self.assertEqual( calc.add(2, 3), -1)

    def tearDown(self):
        self.assertEqual(Calculator.add, Calculator_add)


class HackUnittest(unittest.TestCase): # !

    @classmethod
    def setUpClass(cls):
        cls.unittest_TestCase_run = unittest.TestCase.run
        Config()
        def runfunc(test, result=None):
            get_context()['testing.test'] = test._testMethodName
            unittest.TestCase.run(test, result)

        cls._hacks = PatchSuite( Patch('run', runfunc, unittest.TestCase))
        PatchSuiteStart.handle(cls._hacks)


    def test_with_name(self):
        calc = Calculator()

        with PatchSuite( Patch('add', replace_add, Calculator)):
            self.assertEqual( calc.add(2, 3), -1)
            self.assertEqual(get_context()['testing.test'],
                             'test_with_name')
        self.assertEqual(get_context()['testing.test'], 'test_with_name')


    @classmethod
    def tearDownClass(cls):
        PatchSuiteFinish.handle(cls._hacks)
        assert unittest.TestCase.run == cls.unittest_TestCase_run


## TestConditionalPatches ##

class BadValue(Event):
    pass

class NumberGenerator:
    def generate_number(self):
        return random.randint(0, 1100)

class PatchedGenerator(Patch):
    parent = NumberGenerator

    @patch(wrapper_type=HookWrapper)
    def generate_number(self, return_value):
        if return_value > 1000:
            BadValue.emit(return_value)
        return random.randint(0, 10000)

class Printer:
    printed = []

    @classmethod
    def _print(cls, value):
        #print(value, end=' ')
        cls.printed.append(value)


class PatchedPrinter(SimpleConditionalPatch):

    parent = Printer
    event_to_listen = BadValue

    @patch(attribute='_print')
    def print_stub(cls, value):
        #print(777, end=' ')
        Printer.printed.append(777)

class TestConditionalPatches(unittest.TestCase):

    def setUp(self):
        self._patches = PatchedPrinter.make_patches() + PatchedGenerator.make_patches()
        #import pdb; pdb.set_trace()

        PatchSuiteStart.handle(self._patches)

    def runTest(self):
        printer = Printer()
        generator = NumberGenerator()
        for i in range(50):
            num = generator.generate_number()
            printer._print(num)

        for value in Printer.printed:
            self.assertLessEqual(value, 1000)

    def tearDown(self):
        PatchSuiteFinish.handle(self._patches)
