from django.db import models
from django.db.models.query import QuerySet

from common import get_doc_metadata, contribute_doc_metadata, get_ct
from models import DocType, DocIndexMapping

def peel(s, by):
    """like split(by, 1), except always return a 2-tuple, with the
    remainder of the string empty if it cannot be split any more."""
    ret = s.split(by, 1)
    if len(ret) == 1:
        return ret[0], ''
    else:
        return ret[0], ret[1]


class DocQuerySetMixin(object):
    def _ct(self):
        return get_ct(self.model)

    def dtype(self, **fil):
        """Filter by document type."""
        newfil = {}
        for k, v in fil.iteritems():
            try:
                dt = DocType.objects.get(name=v, content_type=self._ct())
                newfil['%s' % get_doc_metadata(self.model, k, 'type_mfield')] = dt
            except DocType.DoesNotExist:
                pass

        return self.filter(**newfil)

    def dfilter(self, doc_type_name, **fil):
        """Filter by indexed document field."""
        dt = DocType.objects.get(name=doc_type_name, content_type=self._ct())

        newfil = {}
        for k, v in fil.iteritems():
            doc_mfield, rest = peel(k, '__')
            index_mfield = get_doc_metadata(self.model, doc_mfield, 'index_mfield')

            dfield, rest = peel(rest, '__')

            newfil['%s__mapping__dfield' % index_mfield] = dfield
            mapping = DocIndexMapping.objects.get(doc_type=dt, dfield=dfield)

            if rest:
                rest = '__' + rest

            newfil['%s__key_%s%s' % (index_mfield, str(mapping.dfield_type), rest)] = v

        return self.filter(**newfil)


class DocQuerySet(DocQuerySetMixin, QuerySet):
    pass


class DocManagerMixin(object):
    def dtype(self, **fil):
        return self.get_query_set().dtype(**fil)

    def dfilter(self, *args, **fil):
        return self.get_query_set().dfilter(*args, **fil)


class DocManager(models.Manager, DocManagerMixin):
    def get_query_set(self):
        return DocQuerySet(model=self.model)


