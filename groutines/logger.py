
'''
Logger is global as well as many other objects.

Probably will change that in future.
'''

from textwrap import dedent
import os


class EventInfo(object):

    def __init__(self, event, value, where):
        self.event = event
        self.groutine = where
        self.value = value

    def __str__(self):
        head = '%d %s' % (events.index(self) + 1, self.event)
        value = dedent(str(self.value))
        return os.linesep.join( (head, value))

    __repr__ = __str__


class EventsList(list):

    def __str__(self):
        return (2 * os.linesep).join(str(item) for item in self)

events = EventsList()


def clear():
    global events
    events = []

def log(event, value, where):
    info = EventInfo(event, value, where)
    events.append(info)
