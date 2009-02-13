import conf
conf.configure_django(INSTALLED_APPS=('ddb', 'ddb.test'), DEBUG=True)

from django.db import connection
from util import *

import ddb
import ddb.models

import sys
from ddb.test.models import Test

if False:
    t = Test()
    t.d.foo = 'baro'
    t.d.biiz = 'bazz'
    t.dt = 'hello'
    t.save()

    t = Test()
    t.dt = 'hello'
    t.d.foo = 'foo'
    t.save()

    t = Test()
    t.dt = 'another'
    t.d.foo = 'NOPE'
    t.d.bar = 4
    t.d.baz = Storage()
    t.d.baz.GRR = 1
    t.save()

    for i in xrange(100):
        t = Test()
        t.dt = 'yet-one-more'
        t.d.an_int = i
        t.d.a_string = '%d' % i
        t.save()

    ddb.models.DocIndexMapping.create(
        Test, 'd', 'hello', 'foo', 'char_100')

    ddb.models.DocIndexMapping.create(
        Test, 'd', 'another', 'bar', 'integer')

    ddb.models.DocIndexMapping.create(
        Test, 'd', 'another', 'baz.GRR', 'integer')

    ddb.models.DocIndexMapping.create(
        Test, 'd', 'yet-one-more', 'an_int', 'integer')

    ddb.models.DocIndexMapping.create(
        Test, 'd', 'yet-one-more', 'a_string', 'char_100')

import time
start = time.time()

#print ddb.models.Test.objects.all().dfilter('hello', d__foo='foo')
print Test.objects.dfilter('hello', d__foo__contains='o')
print Test.objects.dfilter('another', d__bar__lt=10)
print Test.objects.dfilter('another', **{'d__baz.GRR__gt': 0})
print Test.objects.dfilter('another', **{'d__baz.GRR': 0})

print '**'
from django.db import connection
print Test.objects.dfilter('yet-one-more', d__a_string='9').dfilter('yet-one-more', d__an_int__lt=90)


print time.time() - start
