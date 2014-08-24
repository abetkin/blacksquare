# -*- coding: utf-8 -*-

from util import object_from_name

import greenlet
import types
import itertools
from contextlib import contextmanager
import collections
import wrapt


class ExplicitNone(object): pass

class ForceReturn(object):
    def __init__(self, value):
        self.value = value

class Listener(object):
    '''
    Listens to an event.
    '''
    
    def __init__(self, event, condition=None, groutine=None):
        self.event = event
        self.condition = condition
        self._groutine = groutine or greenlet.getcurrent() # TODO rename
        self.receiver = self._groutine.parent
    
    def switch(self, value=None):
        # check the condition and call groutine.switch()
        #
        if self.condition and not self.condition(value):
            return
        return self._groutine.switch(value)
    
    def send(self, value=None):
        return self.receiver.switch(value)

    def __enter__(self):
        self.event.listeners.add(self)
        return self
    
    def __exit__(self, *exc_info):
        self.event.listeners.remove(self)
    
    def __repr__(self):
        return 'on %(event)s: %(_groutine)s -> %(receiver)' % self.__dict__
        
    __str__ = __repr__


class CallListener(Listener):

    def __init__(self, event, typ='EXIT', condition=None, grinlet=None):
        
        def _condition(value):
            if value.type != typ:
                return
            if condition and not condition(value):
                return
            return True

        super(CallListener, self).__init__(event, _condition, grinlet) 
    
    def __enter__(self):
        if not self.event.callable_wrapper.patched:
            self.event.callable_wrapper.patch()
        return super(CallListener, self).__enter__()
    
    def __exit__(self, *exc_info):
        if not self.event.listeners and self.event.callable_wrapper.patched:
            self.event.callable_wrapper.restore()
        super(CallListener, self).__exit__(*exc_info)

# TODO: __repr__ for classes

class Event(object):
    '''
    An event is uniquely identified by it's name
    and has a set of listeners.
    '''
    instances = {}
    listener_class = Listener
    
    def __new__(cls, key):
        if key in Event.instances:
            return Event.instances[key]
        return super(Event, cls).__new__(cls)

    def __init__(self, key):
        if key in Event.instances:
            return
        self.key = key
        self.listeners = set()
        Event.instances[key] = self
    
    def fire(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], Kwartuple):
            value = args[0]
        else:
            value = Kwartuple(*args, **kwargs)
            
        responses = []
        for listener in tuple(self.listeners):
            listener.receiver = greenlet.getcurrent()
            resp = listener.switch(value)
            responses.append(resp)
        return self.process_responses(responses)
    
    def process_responses(self, values):
        '''
        Process values listeners switch back with
        in response to fired events.
        '''
        for value in values:
            if value is not None: return value
    
    def listen(self, **kwargs):
        '''
        Create a listener. 
        '''
        return self.listener_class(self, **kwargs)
    
    def wait(self, **listener_kwargs):
        '''
        Shortcut. Listens only until the first firing of the event.
        
        Makes values switch with the listener groutine.
        '''
        with self.listen(**listener_kwargs) as lnr:
            return lnr.send()
    
    def __repr__(self):
        return 'Event %s' % self.key
    
    __str__ = __repr__


# TODO rewrite
#@contextmanager
#def listen_any(events, **listener_kwargs):
#    listeners = []
#    for event in events:
#        listener = event.listen(**listener_kwargs)
#        listeners.append(listener)
#        listener.__enter__()
#    yield
#    for listener in listeners:
#        listener.__exit__()
#
#def wait_any(events, **listener_kwargs):
#    with listen_any(events, **listener_kwargs):
#        return switch()

class CallableWrapper(object):
    '''
    Wraps a callable. Calls respective events (``event``) before and after
    the target call. Events sent differ in ``type`` argument:
    'ENTER' and 'EXIT' respectively.
    '''

    def __init__(self, event, target_container, target_attr):
        self.event = event
        self._target_parent = target_container
        self._target_attribute = target_attr
        self._target = getattr(target_container, target_attr)
        self.patched = False


    def patch(self):
        '''
        Replace original with wrapper.
        '''
        try:
            assert isinstance(self._target, types.UnboundMethodType)
            assert isinstance(self._target.__self__, type)
            # if it's a classmethod
            target = classmethod(self._target.__func__)
        except:
            target = self._target
        setattr(self._target_parent, self._target_attribute, self(target))
        self.patched = True
    
    def restore(self):
        '''
        Put original callable on it's place back.
        '''
        setattr(self._target_parent, self._target_attribute, self._target)
        self.patched = False
        
    
    @wrapt.function_wrapper
    def __call__(self, wrapped, instance, args, kwargs):
        self.restore() # restoring original, will patch it back
                       # in the end of this function
        bound_arg = getattr(wrapped, 'im_self', None) \
                    or getattr(wrapped, 'im_class', None)
        enter_info = CallInfo(*args, type='ENTER', callable=wrapped,
                bound_arg=bound_arg, argnames=self.event._argnames, **kwargs)
        enter_value = self.event.fire(enter_info)
        if enter_value is not None:
            return enter_value if enter_value is not ExplicitNone else None

        rv = wrapped(*args, **kwargs)
        exit_info = CallInfo(*args, type='EXIT', callable=wrapped,
                bound_arg=bound_arg, argnames=self.event._argnames, rv=rv, **kwargs)
        exit_value = self.event.fire(exit_info)
        rv = exit_value or rv
        
        self.patch() # patching it back
        
        return rv if rv is not ExplicitNone else None


class FunctionCall(Event):
    '''
    Is fired when target callable is called (event's name is callable's
    import path).
    
    ``callable_wrapper`` is responsible for the respective patching.
    '''

    listener_class = CallListener

    def __new__(cls, key, argnames=None):
        return super(FunctionCall, cls).__new__(cls, key)

    def __init__(self, key, argnames=None):
        if key in Event.instances:
            return
        if isinstance(key, str):
            target_container, target_attr, _ = object_from_name(key) 
        else:
            assert len(key) == 2
            # TODO: probably will be able to figure that out
            #       just from target callable, and get rid of tuple.
            target_container, target_attr = key
        self.callable_wrapper = CallableWrapper(self, target_container,
                                                target_attr)
        self._argnames = argnames
        # Add to events registry in the end
        super(FunctionCall, self).__init__(key)

    def process_responses(self, values_iter):
        values = []
        for value in values_iter:
            if isinstance(value, ForceReturn):
                return value.value
            values.append(value)
        return super(FunctionCall, self).process_responses(values)

    def __repr__(self):
        return 'FCall %s' % self.callable_wrapper._target.__name__
    
    __str__ = __repr__

class Kwartuple(tuple):
    '''
    Tuple which initializes it's __dict__
    with keyword arguments passed to constructor.
    '''
    
    def __new__(cls, *args, **kwargs):
        obj = super(Kwartuple, cls).__new__(cls, args)
        obj.__dict__.update(kwargs)
        return obj


class CallInfo(Kwartuple):

    # TODO: handle default args

    def __new__(cls, *args, **kwargs):
        argnames = kwargs.pop('argnames', None)
        bound_arg = kwargs.pop('bound_arg')
        if argnames:
            delta = len(argnames) - len(args)
            if delta > 0:
                args += tuple(kwargs.pop(argname)
                              for argname in argnames[-delta:])
                # TODO: KeyError: error msg
        if bound_arg:
            args = (bound_arg,) + args
        return super(CallInfo, cls).__new__(cls, *args, **kwargs)

def is_parent(greenlet1, greenlet2):
    g = greenlet2.parent
    while g is not None:
        if g == greenlet1:
            return True
        g = g.parent

class Groutine(greenlet.greenlet):
    
    def __init__(self, *args, **kwargs):
        super(Groutine, self).__init__(*args, **kwargs)
        self.func = self.run

    def __repr__(self):
        try:
            return '%s: %s' % (self.func.__name__, self.__class__.__name__)
        except Exception as exc:
            print exc
            return super(Groutine, self).__repr__()
    
    __str__ = __repr__

## Shortcuts ##

FCall = FunctionCall