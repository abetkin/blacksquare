#!env python3

from patched import PatchSuite, patch
from patched import wrappers
import collections

class StopCounting(PatchSuite):
    class Meta:
        parent = collections.Counter

    @patch(wrapper_type=wrappers.Hook)
    def reset_counts(self, *args, _subtract=collections.Counter.subtract, **kw):
        _subtract(self, **self)

    __init__ = update = subtract = __add__ = __sub__ = __or__ = __and__ = reset_counts

    del reset_counts
#
#if __name__ == '__main__':
#    from unittest import main
import ipdb
with ipdb.launch_ipdb_on_exception():
    with StopCounting():
        c = collections.Counter('animal')
    print( c)
#
#    # pdb fail fast!
#
#    main(verbosity=2,
#         testLoader=test_utils.DebugFailuresTestLoader()
#         )
