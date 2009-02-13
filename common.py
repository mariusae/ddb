from django.contrib.contenttypes.models import ContentType

from decorator import decorator

class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.

        >>> o = storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

    """
    def __getattr__(self, key): 
        try:
            return self[key]
        except KeyError:
            pass

        try:
            return self[unicode(key)]
        except KeyError, k:
            raise AttributeError, k

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k

    def __repr__(self):     
        return '<Storage ' + dict.__repr__(self) + '>'


def memoize(fun):
    memoize_zap_cache(fun)

    def wrapper(fun, *args, **kwargs):
        key = args, frozenset(kwargs.iteritems())

        if not key in fun._cache:
            fun._cache[key] = fun(*args, **kwargs)

        return fun._cache[key]

    return decorator(wrapper, fun)


def memoize_zap_cache(fun):
    fun._cache = {}


def get_ct(model):
    if isinstance(model, type):
        return _get_ct(model)
    else:
        return _get_ct(model.__class__)


@memoize
def _get_ct(model_cls):
    return ContentType.objects.get_for_model(model_cls)


def has_doc_index(model):
    return getattr(model, '_has_doc_index', False)


def get_doc_metadata(model, mfield, key=None):
    meta = getattr(model, '_%s_meta' % mfield, {})
    if key:
        return meta[key]
    else:
        return meta


def contribute_doc_metadata(model, mfield, **kwargs):
    meta = get_doc_metadata(model, mfield)
    meta.update(kwargs)
    setattr(model, '_%s_meta' % mfield, meta)



