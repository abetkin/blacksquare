# -*- coding: utf-8 -*-

'''

@listen('some.function')
def request(rv):
    storage.push(request=rv)


on('other.func').assign(request='self')

rec.depend(req='ctx.a.request')


'''
