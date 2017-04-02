from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.conf import settings as django_settings
from django.conf.urls.defaults import *
from django import forms

import datetime
from djfacet.constants import *

from fb_utils.mymodels import TimeStampedHiddenModel
from fb_utils.utils import blank_or_string, preview_string

from picklefield.fields import PickledObjectField




##################
#  
#  MODELS USED TO CACHE QUERIES, FACET VALUES AND COUNTS
#
##################


class CachedFacetedManager(TimeStampedHiddenModel):
	"""	
	Simple one-field table that contains the pickled backup of the faceted manager instance.
	"""
	manager = PickledObjectField()	# the fields that contains tyhe pickled fm instance value
	




class CachedFacetQuery(TimeStampedHiddenModel):
	"""	 
	an abstraction representing a Django Facet query, run to get the count of available facetValues. 
	
	"""
	facet = models.CharField(max_length=50, verbose_name="the uniquename of the facet")
	resulttype = models.CharField(max_length=50, verbose_name="the uniquename of the result type")
	tot_ids = models.IntegerField(null=True, blank=True, verbose_name="we store the tot number of resulttype objects") 
	# queryargs = models.ForeignKey('CachedQueryArgs', null=True, blank=True,)
	queryargs = models.TextField(null=True, blank=True, verbose_name="Contains a collation of the queryargs IDs - can become pretty big.. so we couldn't use a BIGINT or similar!")
	facetvalues = models.ManyToManyField('CachedFacetValue', null=True, blank=True,)
	
	class Meta:
		pass





class CachedFacetValue(TimeStampedHiddenModel):
	"""	
	Abstraction of facet values, together with their count and all the info necessary for updating the interface in relation to a specific 
		CachedFacetQuery instance
		
	2012-05-23: added extra subs field: "alter table djfacet_cachedfacetvalue add column mpttsubs longtext;"
	"""
	facetvalue = models.CharField(max_length=200, null=True, verbose_name="the name of the value")
	facet = models.CharField(max_length=20, null=True, blank=True, verbose_name="The uniquename of the facet - NOT USED")
	count = models.IntegerField(verbose_name="the count", null=True)
	mpttsubs = models.TextField(null=True, blank=True, verbose_name="If it is an MPTT values, it contains a collation of the sub-values IDs - serialized as a list of strings separate by the '**$**' string. It can become pretty big.. so we couldn't use a BIGINT or similar!")




##################
#  
#  other helper models 
#
##################




class CachedHtmlPage(TimeStampedHiddenModel):
	"""
	Helper table that contains the pickled backup of an html page
	Currently used only for the splash page when it's to large to recalculate each time...	 
	"""
	page = models.CharField(max_length=100, verbose_name="page")
	args = models.CharField(blank=True, max_length=100, verbose_name="auxiliary args - sometimes needed")
	contents = PickledObjectField()


