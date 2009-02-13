from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import PermissionDenied
from django.db.models import sql
from django.db.backends.mysql import base as mysql
import django.db.models.base

from common import get_doc_metadata, contribute_doc_metadata, get_ct, memoize, memoize_zap_cache
import signals

class DocType(models.Model):
    content_type = models.ForeignKey(ContentType)
    name = models.CharField(max_length=60)
    mfield = models.CharField(max_length=60)

    @staticmethod
    @memoize
    def make(name, model, mfield):
        return DocType.objects.get_or_create(
            name=name, content_type=get_ct(model),
            mfield=mfield)[0]

    @staticmethod
    @memoize
    def for_ct(content_type):
        # TODO(marius): become more sophisticated here. Instead of
        # caching+zapping, we really should only be getting post save
        # signals for models that have any sort of relevant mapping,
        # then change the signalling any time mappings are changed.
        return map(None, DocType.objects.filter(content_type=content_type))

    def save(self, **kwargs):
        memoize_zap_cache(DocType.for_ct)
        super(DocType, self).save(**kwargs)

    class Meta:
        unique_together = (('name', 'content_type', 'mfield'),)

    def __unicode__(self):
        return '%s.%s %s:"%s"' % (
            self.content_type.app_label, self.content_type.model, self.mfield, self.name)


FIELD_TYPE_CHOICE = (
    ('char_100',)*2,
    ('integer',)*2,
)

FIELD_TYPE_PY = {
    'char_100': str,
    'integer': int,
}


def coerce_field(field_type, value):
    return FIELD_TYPE_PY[field_type](value)


class DocIndexMapping(models.Model):
    @staticmethod
    def mappings(model=None, doc_mfield=None, doc_type_name=None, dfield=None):
        fil = {}
        if model:
            fil['doc_type__content_type'] = get_ct(model)
        if doc_mfield:
            fil['doc_type__mfield'] = mfield
        if doc_type_name:
            fil['doc_type__name'] = doc_type_name
        if dfield:
            fil['dfield'] = dfield

        return DocIndexMapping.objects.filter(**fil)


    @staticmethod
    def create(model, doc_mfield, doc_type_name, dfield, dfield_type):
        dt = DocType.objects.get(name=doc_type_name,
                                 content_type=get_ct(model),
                                 mfield=doc_mfield)

        DocIndexMapping.objects.get_or_create(
            doc_type=dt, dfield=dfield, dfield_type=dfield_type)

    ImmutableError = django.db.models.base.subclass_exception(
        'ImmutableError', PermissionDenied, __name__)

    doc_type = models.ForeignKey(DocType)
    dfield = models.CharField(max_length=80)
    dfield_type = models.CharField(max_length=15, choices=FIELD_TYPE_CHOICE)

    def maybe_index_doc(self, obj, new_mapping=False):
        # A simple typecheck first: refuse to index a document if it's
        # of the wrong type.
        type_mfield = get_doc_metadata(
            obj.__class__, self.doc_type.mfield, key='type_mfield')

        if getattr(obj, type_mfield) != self.doc_type.name:
            return False

        # Find the field name
        parts = self.dfield.split('.')
        doc = getattr(obj, self.doc_type.mfield)

        try:
            value = reduce(lambda doc, p: doc[p], parts, doc)
        except KeyError:
            # Option to be strict?
            return False

        # We cannot refer to `content_object' directly, see:
        # http://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/

        ct = get_ct(obj.__class__)

        if new_mapping:
            r = DocIndexRow(mapping=self, content_type=ct, object_id=obj.id)
        else:
            try:
                r = DocIndexRow.objects.get(
                    mapping=self, content_type__pk=ct.id,
                    object_id=obj.id)
            except DocIndexRow.DoesNotExist:
                r = DocIndexRow(mapping=self, content_type=ct, object_id=obj.id)

        setattr(r, 'key_%s' % self.dfield_type, coerce_field(self.dfield_type, value))
        r.save()

        return True

    def save(self, force_insert=False, force_update=False):
        if self.pk:
            raise self.ImmutableError, (
                '%s objects are immutable once created' % self.__class__.__name__)

        super(DocIndexMapping, self).save(
            force_insert=force_insert, force_update=force_update)

        # Now, index existing fields.
        cls = self.doc_type.content_type.model_class()

        for obj in cls.objects.dtype(**{self.dfield: self.doc_type}):
            self.maybe_index_doc(obj, new_mapping=True)

        # Finally make sure we get the right set of hooks after
        # creating the mapping.
        signals.maybe_connect(cls)

    class Meta:
        unique_together = (('doc_type', 'dfield', 'dfield_type'),)

    def __unicode__(self):
        return '%s: %s:%s' % (
            repr(self.doc_type), self.dfield, self.dfield_type)


class DocIndexRow(models.Model):
    mapping = models.ForeignKey(DocIndexMapping)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    key_char_100 = models.CharField(max_length=100, db_index=True, null=True)
    key_integer = models.IntegerField(db_index=True, null=True)

    class Meta:
        unique_together = (
            ('mapping', 'content_type', 'object_id', 'key_char_100', 'key_integer'),
        )

    def __unicode__(self):
        return '%s: %s' % (
            repr(self.mapping), getattr(self, 'key_%s' % self.mapping.dfield_type))

