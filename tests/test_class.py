#!env python3
import sys
import unittest
import random
import logging

from blacksquare import Config as BaseConfig
from blacksquare.core.events import Event

from blacksquare.patching import Patch, patch, SimpleConditionalPatch
from blacksquare.patching.base import (HookWrapper, InsertionWrapper)
from blacksquare.patching.handlers import PatchSuitesStack, GlobalPatches
from blacksquare.patching.events import PatchSuiteStart, PatchSuiteFinish
from blacksquare import get_config, get_storage

from blacksquare.core.objects import Logger
from blacksquare.patching.suite import PatchSuite
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
