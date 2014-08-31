# -*- coding: utf-8 -*-

import os
import re
from .util import object_from_name
from .dec import GroutineFunction

class DefaultFinder(object):
    
    modules = None
    base_dir = None
    regexp = r'gro\w*\.py'
    
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.modules = self.modules or []
    
    def discover(self):
        base_dir = self.base_dir or os.getcwd()
        groutines = set()
        if not self.modules:
            for path, dirs, files in os.walk(base_dir):
                for fname in files:
                    if not re.match(r'\w+\.py$', fname) or not re.match(self.regexp, fname):
                        continue
                    relpath = os.path.relpath(path, base_dir)
                    if relpath != '.':
                        parts = relpath.lstrip('.').split(os.path.sep)
                    else:
                        parts = []
                    # probably exists a more elegant solution for import
                    obj_path = '.'.join(parts + [fname[:-3]])
                    _, _, mod = object_from_name(obj_path)
                    self.modules.append(mod)
        for mod in self.modules:
            for attr in dir(mod):
                if isinstance(getattr(mod, attr), GroutineFunction):
                    groutines.add(getattr(mod, attr))
        return groutines

if __name__ == '__main__':
    
    finder = DefaultFinder()
    gs = finder.discover()
    print (gs)