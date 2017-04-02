
"""
Django Extensions additional model fields
"""

from django.db.models import DateTimeField, CharField
import datetime
import re

try:
    import uuid
except ImportError:
    from django_extensions.utils import uuid


class CreationDateTimeField(DateTimeField):
    """ CreationDateTimeField 
    
    By default, sets editable=True, blank=True, default=datetime.now
    """
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', True)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('default', datetime.datetime.now)
        DateTimeField.__init__(self, *args, **kwargs)
    
    def get_internal_type(self):
        return "DateTimeField"

class ModificationDateTimeField(CreationDateTimeField):
    """ ModificationDateTimeField 
    
    By default, sets editable=True, blank=True, default=datetime.now
    
    Sets value to datetime.now() on each save of the model.
    """
    
    def pre_save(self, model, add):
        value = datetime.datetime.now()
        setattr(model, self.attname, value)
        return value
    
    def get_internal_type(self):
        return "DateTimeField"


