from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from common import memoize, Storage, get_doc_metadata, contribute_doc_metadata, get_ct
from models import DocType, DocIndexRow
import json

# To ensure that you are properly initialized:
import ddb

class DocField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, dict):
            return value
        elif value is None or value == '':
            return Storage()
        else:
            return Storage(json.decode(value))

    def get_db_prep_value(self, value):
        return json.encode(value)


# We hide the complexity of doc types by just making them appear as
# string.
class DocTypeField(models.ForeignKey):
    def __init__(self, mfield, **kwargs):
        super(DocTypeField, self).__init__(DocType, **kwargs)
        self.__mfield = mfield

    def contribute_to_class(self, cls, name):
        super(DocTypeField, self).contribute_to_class(cls, name)
        attr = cls.__dict__[name]

        mfield = self.__mfield

        class Proxy(object):
            def __get__(self, obj, type=None):
                try:
                    return attr.__get__(obj, type).name
                except DocType.DoesNotExist:
                    return ''

            def __set__(self, obj, value):
                dt = DocType.make(name=value, model=cls, mfield=mfield)
                attr.__set__(obj, dt)

        setattr(cls, name, Proxy())

        contribute_doc_metadata(cls, self.__mfield, type_mfield=name)


class DocIndex(generic.GenericRelation):
    def __init__(self, mfield, doc_type_mfield):
        super(DocIndex, self).__init__(DocIndexRow)
        self.__mfield = mfield

    def contribute_to_class(self, cls, name):
        super(DocIndex, self).contribute_to_class(cls, name)
        contribute_doc_metadata(cls, self.__mfield, index_mfield=name)
        setattr(cls, '_has_doc_index', True)
