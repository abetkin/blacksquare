# -*- coding: utf-8 -*-

'''
Here live decorators.
'''

def groutine(event=None, once=True):
    '''
    Lazy decorator. Does nothing, just stores arguments.
    
    ``once`` means groutine will be run only at first firing of the event.
    '''
    def decorator(f):
        f._groutine = {'event': event, 'once': once}
        return f
    return decorator