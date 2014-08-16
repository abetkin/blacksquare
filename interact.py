# -*- coding: utf-8 -*-

#from groutines import switch

#class Interact(object):
#    
#    def __init__(self, scen):
#        self.scen = scen
#    
#    def greenlet(self):
#        while True:
#            1
#
#    def __iter__(self):
#        return self
#    
#    def next(self):
#        return switch()

from greenlet import greenlet


class genlet(greenlet):

    func = None
    args = None
    kwargs = None

#    def __init__(self, *args, **kwds):
#        self.args = args
#        self.kwds = kwds

    main_running = False
#
#    def wait(event, **kw):
#        with event.listen(**kw):
#            

    def wait(self, event, **kw):
        with event.listen(grinlet=self, **kw) as lnr:
            return lnr.switch2parent()

    def run(self):
        while True:
            self.func(*self.args, **self.kwargs)

    def __iter__(self):
        return self
    
#    def __call__(self, f, args=(), kwargs={}):
#        self.func = f
#        self.args = args
#        self.kwargs = kwargs
#        if not self.main_running:
#            gr_f = greenlet(f)
#            sce.greenlet.switch()
#            self.main_running = 1
#            self.parent = greenlet.getcurrent()
#        result = self.switch()
#        if self:
#            return result
#        else:
#            raise StopIteration

#    def __next__(self):
#        self.parent = greenlet.getcurrent()
#        result = self.switch()
#        if self:
#            return result
#        else:
#            raise StopIteration

from groutines import *

class SomeClass(object):
    
    def __init__(self):
        self.a = 1
    
    def start(self):
        return 1
    
    @classmethod
    def middle(cls, default=2):
        return default
    
    def end(self):
        return 1

EV = FunctionCall((SomeClass, 'middle'),
                       argnames=['default']
                       )#.wait()

@Groutine()
def a_greenlet():
    global EV
    val = EV.wait()
#    val = FunctionCall((SomeClass, 'middle'),
#                       argnames=['default']
#                       ).wait()
#        from pdb import Pdb
#        Pdb().set_trace(groutines_all['big_value'].gr_frame)
    print val
#        evt = FunctionCall('__main__.SomeClass.middle').wait()
    for i in range(5):
        e = Event('OLD_VALUE')
        print e.fire(value=i)
    switch(ForceReturn(9))
    

@Loop(Event('OLD_VALUE'))
def big_value(value):
    return (value + 1)

from functools import wraps

def scenario(func):
    @wraps(func)
    def wrapper(*args, **kw):
        greenlet.getcurrent().parent.switch()
        return func(*args, **kw)
    return Groutine()(wrapper)

@scenario
def sce():
    o = SomeClass()
    print SomeClass.middle(default=6)

if __name__ == '__main__':
    for gr in [a_greenlet, big_value, sce]:
        gr.start()
    gg = genlet()
    gg.parent = sce.greenlet
    print gg.wait(EV)
    
    