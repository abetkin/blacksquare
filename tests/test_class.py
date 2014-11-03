#!env python3
import sys
import unittest
import random
import logging

from patched import Config as BaseConfig
from patched.core.events import Event

from patched.patching import Patch, patch, SimpleConditionalPatch
from patched.patching.base import (HookWrapper, InsertionWrapper)
from patched.patching.handlers import PatchSuitesStack, GlobalPatches
from patched.patching.events import PatchSuiteStart, PatchSuiteFinish
from patched import get_config, get_storage

from patched.core.objects import Logger
from patched.patching.suite import PatchSuite
from tests import utils as test_utils

class Base:

    def __init__(self):
        self.val = 1

class Class(Base):

    def __init__(self):
        super().__init__()
        self.val += 1

Class_orig = Class

class SwapClass(PatchSuite):

    class Meta:
        parent = Class

    #@patch(wrapper_type=InsertionWrapper)
    #def __new__(cls):
    #    return ()

    @patch()
    def __init__(self):
        self.val = 5


class TestClass(unittest.TestCase):

    #def setUp(self):
    #    self.assertEqual(Class, Class_orig)

    def test_1(self):
        with SwapClass():
            obj = Class()
            self.assertEqual(obj.val, 5)
        self.assertEqual(Class().val, 2)

    #def tearDown(self):
    #    self.assertEqual(Class, Class_orig)




if __name__ == '__main__':
    from unittest import main
    #import ipdb
    #with ipdb.launch_ipdb_on_exception():

    # pdb fail fast!

    main(verbosity=2,
         testLoader=test_utils.DebugFailuresTestLoader()
         )
