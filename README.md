patched: use the localhost correctly!
========

``patched`` is a mini-framework for patching with emphasis on simplicity, relative safety and human-oriented interface.
In regard of patching,
what it allows is basically to replace any callable with a user-defined one.

Hopefully that features make it useful not only for patching, but also logging, debugging, testing.

It aims to make equally easy to write a couple of throw-away patches or to store modules of debug patches
(or mocks for local development) that others can use without looking at their code. And oh yes, it's not only about patching..


### How to install

The package can be installed from PyPI but it's in active development and I'm afraid it won't be updated frequently enough. So use

    $ pip3 install -e git+git@github.com:abetkin/patched.git#egg=patched

**Attention: currently works only with python 3**

The package size is 600 SLOC so don't fear and have a look at the code!

**[Documentation.](http://nbviewer.ipython.org/github/abetkin/patched/blob/master/docs/main.ipynb)**

