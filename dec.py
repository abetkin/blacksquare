# -*- coding: utf-8 -*-

'''
Here live decorators.
'''

def groutine(event=None, once=True, listener_kwargs={}):
    '''
    Marks groutine (lazy decorator).
    
    Common case is to use it without arguments::
    
        @groutine()
        def some_statements():
            ...
    
    Non-default arguments arguments can be used to reduce boilerplate
    in groutine definition. In this case you should specify the event
    groutine should listen to. Decorated function arguments (*args and **kwargs)
    are the value of the event fired.
    
    Eg., the code below defines a groutine that will be executed
    on every firing of the event::
    
        @groutine(event=Event('BOOM'), once=False)
        def boom(location, strength, **kw):
            print '%s: BOOM!' % location
    
    :param once: groutine will be run only at first firing of the event
    '''
    def decorator(f):
        f._groutine = {'event': event,
                       'once': once,
                       'listener_kwargs': listener_kwargs}
        return f
    return decorator