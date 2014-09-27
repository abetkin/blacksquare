from .local import tlocal

class Logger(list):

    @classmethod
    def instance(cls):
        if not hasattr(tlocal, 'logger'):
            tlocal.logger = cls()
        return tlocal.logger


class CallRecord(object):
    '''
    Record about function call.
    '''

    def __init__(self, call_args, rv):
        self.call_args = call_args
        self.rv = rv
