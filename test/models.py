from django.db import models

from ddb.fields import DocField, DocTypeField, DocIndex
from ddb.manager import DocManager

class Test(models.Model):
    d = DocField()
    dt = DocTypeField('d')
    di = DocIndex('d', 'dt')

    objects = DocManager()

    def __unicode__(self):
        return '%s: %s' % (self.dt, repr(self.d))

