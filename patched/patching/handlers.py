from ..core.threadlocal import ThreadLocalMixin

#FIXME: Logger() on start
class PatchSuitesStack(ThreadLocalMixin):
    '''
    Class contains handlers for starting and finishing the execution of
    a suite with patches.

    The implementation below is the recomended one and accumulates suites
    with patches in a stack, when the suite execution finished, its patches
    are unapplied and it is popped from the stack.
    '''

    global_name = 'config.controller'

    def __init__(self):
        self.suites_stack = []

    def suite_start(self, suite):
        self.suites_stack.append(suite)
        for patch in suite:
            patch.on()

    def suite_finish(self, suite):
        top_suite = self.suites_stack.pop()
        assert top_suite == suite, '%s suite should be on top, found %s' % (
                suite, top_suite)
        for patch in reversed(top_suite):
            patch.off()


class GlobalPatches(ThreadLocalMixin):
    '''
    Class contains handlers for starting and finishing the execution of
    a suite with patches.

    All patches are unapplied only when the last suite has finished execution.
    '''

    global_name = 'config.controller'

    def __init__(self):
        self.patches = []
        self.root_suite = None

    def suite_start(self, suite):
        self.patches.extend( suite)
        if not self.root_suite:
            self.root_suite = suite
        for patch in suite:
            patch.on()

    def suite_finish(self, suite):
        if suite != self.root_suite:
            return
        for patch in reversed(self.patches):
            patch.off()
        self.root_suite = None
