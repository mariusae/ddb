"""DDB is a document store using django models.

We provide a Document field that can be added to any django model, and
you automatically get:

  - document (de)serialization to/from JSON
  - selective field indexing
  - type management"""

from django.db.models.loading import get_models
from django.db.models.signals import class_prepared

from signals import maybe_connect

def class_prepared_handler(sender, **kwargs):
    maybe_connect(sender)

map(maybe_connect, get_models())

# For any new ones that might occur after initialization.
# class_prepared.connect(class_prepared_handler)

