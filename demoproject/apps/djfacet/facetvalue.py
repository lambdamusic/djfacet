#!/usr/bin/python 
# -*- coding: utf-8 -*-

from string import printable as POSSIBLE_CHARACTERS  # '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r\x0b\x0c'
from django.utils.encoding import force_unicode

from fb_utils.utils import djfacetlog
from djfacet.constants import *



#
# FacetValue: abstracts the values within a facet 
#


class FacetValue(object):
	"""A FacetValue is an element within a facet. 
		=+=
		Name = name of the value used to filter the information space (whithin a facet)
		Displayname = in some cases the displayed name might be different
		Mask = dictionary used for passing sets of displayNames, in the form of mappings between 'names' and other values. 
				This is useful if we want to assing displaynames programmatically, e.g. all 'names' between 1 and 10 
				Syntax:	 original_value_in_dbfield : 'displayname'
					'mask' : {1 : 'Royal Charters', 
							  2 : 'Ecclesiastical charters',
							  3 : 'Aristocratic and other private charters',},
		father = contains the ID of the father (0 represents the top level).
		XXX hierarchytype = a string, 'alpha' or 'range' for now
		XXX hierarchyextra = other info required for the hierarchy (not standardized at the moment)
		customvalues = a dict used to compose the behaviour-query for a facetvalue 
						eg: {'hammondnumber' : 1, 'hammondnumb2__gt' : 0, 'hammondnumb2__lt' :10}
						
		rootfather = TODO				
						
		=+=
	
	"""
	def __init__(self, name, facet, father=0, hierarchytype="", hierarchyextra=None, number_opts= None, show_singlefacet_header=True, displayname="", 
					mask=None, customvalues=None, howmany=0, rootfather=None, mpttoriginalID = None, mptt_treeID = None ):
		self.name = name
		self.facet = facet
		self.hierarchytype = hierarchytype	# a string
		self.hierarchyextra = hierarchyextra  
		self.number_opts = number_opts or {}
		self.show_singlefacet_header = show_singlefacet_header
		self.displayname = displayname or name
		self.mask = mask
		self.customvalues = customvalues
		self.howmany = howmany
		if father:
			self.father = father.id
		else:
			self.father = 0
		self.rootfather = rootfather
		self.mpttoriginalID = mpttoriginalID  # needed for getting bck to the MPTT instance and speeding up searches
		self.mptt_treeID = mptt_treeID  # for faster searches on trees
		self.id = self.__constructID(name, facet.uniquename)	# the unique ID python gives to every obj
		# set up the mask
		if self.mask:
			if self.mask.get(self.name):
				self.displayname = self.mask.get(self.name)
		


	def __constructID(self, name, facetuniquename):
		""" Method that calculates a unique id for each facetvalue, for better identification.
			This consitutes a non-stochastic method to maintain the IDs of values across systems, and thus being able to
			pass around URL-queries for the faceted browser.
			Note that an ID for faceted browser values is not related at all to the ID of the object in the database!
			
			DJF_URL_AS_NUMBERS = False:
				A combination of facet uniquename and value name must be unique: eg 'religionname_Protestant'
				
			DJF_URL_AS_NUMBERS = True:
				We take the string above and transform it into a number.
			 
		 """
		exit = ""
		if DJF_URL_AS_NUMBERS:
			bigstring = force_unicode(name) + force_unicode(facetuniquename)
			for el in bigstring.replace(" ", ""):
				try:
					exit += force_unicode(POSSIBLE_CHARACTERS.find(el) + 1)
				except:
					exit += '999'
			return int(exit)
		else:
			bigstring = force_unicode(facetuniquename) + u"_" + force_unicode(name)
			return bigstring.replace(" ", "")
				
		



