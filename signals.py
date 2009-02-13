"""deal with signalling for ddb"""

from django.db.models.signals import post_save, post_delete

from common import has_doc_index, get_ct
from models import DocType

def has_mapped_doc_index(model):
    if not has_doc_index(model):
        return False

    for dt in DocType.for_ct(get_ct(model)):
        if dt.docindexmapping_set.count() > 0:
            return True
    else:
        return False


def maybe_connect(model):
    if has_mapped_doc_index(model):
        post_save.connect(post_save_handler, sender=model)
        post_delete.connect(post_delete_handler, sender=model)


def post_save_handler(sender, **kwargs):
    instance = kwargs['instance']

    # Find mappings & (re-)index the instance for all of them.
    for dt in DocType.for_ct(get_ct(instance)):
        for mapping in dt.docindexmapping_set.all():
            mapping.maybe_index_doc(instance)


def post_delete_handler(sender, **kwargs):
    pass

