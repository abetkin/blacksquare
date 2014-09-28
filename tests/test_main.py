
import unittest

from blacksquare.config import Config
from blacksquare.patch import Patch, patch
from blacksquare.manager import PatchManager

from blacksquare.util import import_obj

def make_patch(import_path, *args, **kw):
    parent, attr, _ = import_obj(import_path)
    return Patch(parent, attr, *args, **kw)


class MyConfig(Config):

    def get_patches(self):
        return [
            #Patch(calc, 'add', replace_add)
        ]

class Calculator:

    def add(self, a, b):
        return a + b

class ReplaceAdd(Calculator, metaclass=patch):

    def add(self, a, b):
        return a - b

#def replace_add(self, a, b):
#    return a - b

if __name__ == '__main__':
    global calc
    calc = Calculator()

    pm = PatchManager(ReplaceAdd())
    with pm:

        print( calc.add(2, 3))
