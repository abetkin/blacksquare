Patching: the white people method
=================================

With this I introduce **groutines** framework.
It's aim is to see what runtime-controlled patching can bring us. In my opinion, that idea wasn't fully exploited yet.

It supports only patching callables, but it's done implicitly for you, all your code needs to do is to subscribe at runtime to the event of calling some method. Custom events are also supported.

About the code you need to write: it is supposed to be structured into groutines, an independent, discoverable (something like a test) piece of code. As opposed to tests, they are alive altogether (not run one by one) and can fire and listen to events.

how it appeared
----------------

The initial aim was to give tests the ability to "listen" to some method so that to add checks on its parameters and the return value. As later the range where it could be possibly applied widened, I focused on implementing the core functionality, so there is no any integration with testing at all in the current version.

range of application
---------------------
Everywhere except production: testing, debugging, logging, writing code, etc.

global scenario
-----------------

The framework is lazy: it does not run code itself, instead, it (temporary) patches external code's functions so that it's code would be run. This "external scenario" can be it a script, a test, or a server responding on user request. It is not required to know anything about the framework.

groutine
----------

In current version it is just a [greenlet](http://greenlet.readthedocs.org), i. e., the execution context which can be given control by switching into it. But, unlike the function, 2 greenlets can switch data back and forth many times, and unlike the generator, any greenlet has a parent, etc. *Greenlets are executed in the same thread with the rest of the program, there is no event loop occupying a thread.*

Groutine is a relatively independent unit in the framework. In most cases they just respond to and fire the events (events carry data), also can directly switch data with the parent. They serve the main goal of the framework: to be able to test (or debug, or log) logically unrelated stuff separately. Or conversely, to put logically correlated stuff together.
