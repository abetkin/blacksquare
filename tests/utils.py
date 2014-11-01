
import sys
from contextlib import contextmanager
from unittest import loader, case, suite, util
from functools import wraps
import ipdb

@contextmanager
def launch_ipdb_on_exception():
    try:
        yield
    except Exception:
        e, m, tb = sys.exc_info()
        print(m.__repr__(), file=sys.stderr)
        ipdb.post_mortem(tb)
        raise


def ipdb_on_exception(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        with launch_ipdb_on_exception():
            return func(*args, **kwds)
    return wrapper

class DebugFailuresTestLoader(loader.TestLoader):

    def loadTestsFromTestCase(self, testCaseClass):
        if issubclass(testCaseClass, suite.TestSuite):
            raise TypeError("Test cases should not be derived from "
                            "TestSuite. Maybe you meant to derive from "
                            "TestCase?")
        testCaseNames = self.getTestCaseNames(testCaseClass)
        if not testCaseNames and hasattr(testCaseClass, 'runTest'):
            testCaseNames = ['runTest']

        def test_functions():
            for method_name in testCaseNames:
                test_func = getattr(testCaseClass, method_name)
                yield method_name, ipdb_on_exception(test_func)
        # TODO: instantiate class in orig. module
        testcase_class = type('Pdb' + testCaseClass.__name__, (testCaseClass,),
                              dict(test_functions()))
        return self.suiteClass(map(testcase_class, testCaseNames))


