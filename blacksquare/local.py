
import threading

from collections import defaultdict


#TODO possibly wrap this in a class
def _tree():
    return defaultdict(_tree)

tlocal = threading.local()

def get_tree():
    if not hasattr(tlocal, 'tree'):
        tlocal.tree = _tree()
    return tlocal.tree


