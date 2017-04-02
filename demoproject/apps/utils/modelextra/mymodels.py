"""
Django Extensions abstract base model classes.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

import utils.modelextra.myfields as myfields



# the hierarchy: 

# ++TimeStampedHiddenModel
# ++TimeStampedModel
# ++++++AuthorityListModel
# ++++++DefaultModel
# ++++++++++DefaultAuthorityList



class TimeStampedHiddenModel(models.Model):
	""" TimeStampedModel
	An abstract base class model that provides self-managed "created" and
	"modified" fields, but they both are HIDDEN by default - so they won't show in the admin!
	Use it for many-to-many models usable as inlines....
	"""
	created_at = myfields.CreationDateTimeField(_('created'), 
				help_text="Do not modify. The time this record was firstly created.", editable=False)
	updated_at = myfields.ModificationDateTimeField(_('modified'), 
				help_text="No need to edit: automatically updated each time the record is saved.", editable=False)
	
	class Meta:
		abstract = True

class TimeStampedModel(models.Model):
	""" TimeStampedModel
	An abstract base class model that provides self-managed "created" and
	"modified" fields.
	"""
	created_at = myfields.CreationDateTimeField(_('created on date'), 
				help_text="The time this record was firstly created. Do not modify.")
	updated_at = myfields.ModificationDateTimeField(_('modified on date'), 
				help_text="Automatically updated each time the record is saved.")
	
	class Meta:
		abstract = True

class AuthorityListModel(TimeStampedModel):
	""" AuthorityListModel
	An abstract base class model that provides the common fields used in authority lists, 
	and also the self-managed "created" and "modified" fields.
	"""
	name = models.CharField(max_length=765)
	description = models.TextField(blank=True)

	class Meta:
		abstract = True
		ordering = ["name"]



class EnhancedModel(TimeStampedModel):
	""" DefaultModel
	An abstract base class model that provides self-managed "created", 
	"modified", and "user creation" fields. Also, we provide the fields needed for the 
	'administration' features needed by the editors
	"""
	# ADMINISTRATION section
	editedrecord = models.BooleanField(default=False, verbose_name="edited record?", 
		help_text="Tick to indicate that this record has been finalized")
	review = models.BooleanField(default=False, verbose_name="review", 
		help_text="Tick to indicate that this record is under review by the editorial team")
	internal_notes = models.TextField(blank=True, verbose_name="internal_notes")
	created_by = models.ForeignKey(User, blank=True, null=True, related_name="created_%(class)s", 
		editable = True, help_text="No need to edit: automatically set when saving")
	updated_by = models.ForeignKey(User, blank=True, null=True, related_name="updated_%(class)s", 
		editable = True, help_text="No need to edit: automatically set when saving")

	# Added on Aug3 as a generic method to access everything about a model in the templates"""
	def attrs(self):
		items = [(k, v) for k, v in self.__dict__.items()]
		items.sort()
		return items
		# for attr, value in self.__dict__.iteritems():
		#	yield attr, value

	class Meta:
		abstract = True			





class EnhancedAuthorityList(EnhancedModel):
	""" AuthorityListModel
	An abstract base class model that provides the common fields used in authority lists, 
	the self-managed "created" and "modified" fields, and the fields needed for the 'administration' features
	needed by the editors
	"""
	name = models.CharField(max_length=765)
	description = models.TextField(blank=True)

	class Meta:
		abstract = True
		ordering = ["name"]






