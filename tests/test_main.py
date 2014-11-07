#!env python3
import unittest
import random
import logging

from patched import Config as BaseConfig
from patched.core.events import Event

from patched.patching import Patch, patch, PatchSuite, wrappers

from patched.patching.base import SimpleConditionalPatch
from patched.patching.handlers import PatchSuitesStack, GlobalPatches
from patched.patching.events import PatchSuiteStart, PatchSuiteFinish
from patched import get_config, get_storage

from patched.core.objects import Logger

from tests import utils as test_utils


class Calculator:

    def add(self, a, b):
        return a + b

Calculator_add = Calculator.add

class BrokenCalculator(PatchSuite):
    class Meta:
        parent = Calculator

    @patch(wrapper_type=wrappers.Insertion)
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
        return super().run(result)




class Simplest(TestCase):

    def setUp(self):
        self.assertEqual(Calculator.add, Calculator_add)

    def runTest(self):
        calc = Calculator()
        patches = ( Patch('add', Calculator, wrapper_func=replace_add),)
        with PatchSuite(patches):
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
        patches = ( Patch('add', Calculator, wrapper_func=replace_add),
                        )
        with PatchSuite(patches):
            self.assertEqual( calc.add(2, 3), -1)
            with BrokenCalculator():
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
        patches = ( Patch('add', Calculator, wrapper_func=replace_add),)
        with PatchSuite(patches):
            self.assertEqual( calc.add(2, 3), -1)
            with BrokenCalculator():
                self.assertAlmostEqual( calc.add(2, 3), 5.5)
                #import ipdb; ipdb.set_trace()

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
        patches = ( Patch('add', Calculator, wrapper_func=replace_add),
                        )
        with PatchSuite(patches):
            self.assertEqual( calc.add(2, 3), -1)

        out = str(Logger.instance())
        self.assertEqual(out, 'Logged events:\n0| Call to add ( => replace_add)')

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
        ctx = _globals['get_storage']()
        self.assertEqual(ctx['my.var'], 'my.value')
        self.assertEqual(_locals['ret'], -1)

    def runTest(self):
        get_storage()['my.var'] = 'my.value'
        calc = Calculator()
        patches = ( Patch('add', Calculator, wrapper_func=replace_add),
                        )
        with PatchSuite(patches):
            self.assertEqual( calc.add(2, 3), -1)

    def tearDown(self):
        self.assertEqual(Calculator.add, Calculator_add)


class HackUnittest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.unittest_TestCase_run = unittest.TestCase.run
        Config()
        def runfunc(test, result=None):
            get_storage()['testing.test'] = test._testMethodName
            unittest.TestCase.run(test, result)
        patches = (Patch('run', unittest.TestCase, wrapper_func=runfunc),)
        cls._hacks = PatchSuite(patches)
        PatchSuiteStart.handle(cls._hacks)


    def test_with_name(self):
        calc = Calculator()
        patches = ( Patch('add', Calculator, wrapper_func=replace_add),
                        )
        with PatchSuite(patches):
            self.assertEqual( calc.add(2, 3), -1)
            self.assertEqual(get_storage()['testing.test'],
                             'test_with_name')
        self.assertEqual(get_storage()['testing.test'], 'test_with_name')


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

class PatchedGenerator(PatchSuite):
    class Meta:
        parent = NumberGenerator

    @patch(wrapper_type=wrappers.Hook)
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


class PatchedPrinter(PatchSuite):
    class Meta:
        parent = Printer
        listen_to = BadValue
        patch_type=SimpleConditionalPatch

    @patch(attribute='_print')
    def print_stub(cls, value):
        #print(777, end=' ')
        Printer.printed.append(777)

class TestConditionalPatches(unittest.TestCase):

    def setUp(self):
        self._patches = PatchedPrinter() + PatchedGenerator()
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

##

class TestBindToInstance(unittest.TestCase):

    def runTest(self):
        calc = Calculator()

        @patch(parent=calc, attribute='add')
        def replace_add(inst, a, b):
            return max(a, b)

        with PatchSuite([replace_add.make_patch()]):
            self.assertEqual( calc.add(2, 3), 3)
        self.assertEqual( calc.add(2, 3), 5)



# TODO: add tests for multiple threads



if __name__ == '__main__':
    from unittest import main
    #import ipdb
    #with ipdb.launch_ipdb_on_exception():

    # pdb fail fast!

    main(#module=__file__[:-3],
         verbosity=2,
         testLoader=test_utils.DebugFailuresTestLoader()
         )
