from django.db.models import Avg, Max, Min, Count, Q

from facetvalue import *
from fb_utils.utils import *

from djfacet.constants import *





		
#
# Facet class : abstracts a single facet ('color') within a group ('car') 
#

class Facet(object):
	""" A Facet is a collection of facet-values. 
		It can be defined programmatically as the set of values an attribute of a django-model has.
		=+=
		name = the label of the facet that gets displayed
		facetvalues = a list of facetvalues objects
		originalModel = the django model that the facet depends on (if there's one)
		originalAttribute = the model field used for creating/querying facet-values ['surname' for the 'Person' model]
		displayAttribute = the model field used for displaying facet-values	 [e.g. 'full surname' for the 'Person' model]
		behaviour = definition of the query-paths to each of the result-types. A list of dicts: 
						# 'behaviour' : [ {'resulttype' : 'people', 
						#				   'querypath' : "",
						#				 'explanation' : "showing all people with selected surname " } ,
						#				{'resulttype' : 'people', 
						#				 'querypath' : "",
						#				 'explanation' : "showing all people with selected surname " }
						#				]
		hierarchyoptions = a dict that describes if facetvalues need to be organizes in hierarchies
							eg: hier.. = {'alpha' : True, 'numrange' : .....} etc. in the future this dict should contain 
							more options for hand-made hierarchied we might want to use...
		mask = a dictionary that maps specific values to 'displaynames' (see above). 
				It is passed as it is to the FacetValue object
		customvalues = a dict of label + inner dict. The inner dict is the one passed to the FacetValue object to create the 
						the behaviour-query for a specific label. (no hierachical data for now)
						eg. 
					{
					'charters of the kings of Scots' : 
						{'hammondnumber' : 1, 'hammondnumb2__gte' : 1, 'hammondnumb2__lte' :9},
					'charters of the queens of Scots' : 
						{'hammondnumber' : 1, 'hammondnumb2__gte' : 10, 'hammondnumb2__lte' :12} }
						
		hierarchy = True of False, refers to whether we're using an mptt model 
		TODO FIX THE NAMING!!!
		
		2012-08-08:
		added number_opts=self.number_opts
		added show_singlefacet_header=self.show_singlefacet_header
		
		=+=
	"""
	def __init__(self, uniquename, name, originalModel, originalAttribute, displayAttribute = None, ordering = None, behaviour = None, hierarchyoptions= None, number_opts = None, mask=None, customvalues = None, mptt = False, explanation = "", exclude=False, group=[], show_singlefacet_header=True):
		self.uniquename = uniquename
		self.name = name
		self.originalModel = originalModel
		self.originalAttribute = originalAttribute
		self.displayAttribute = displayAttribute
		self.ordering = ordering
		self.behaviour = behaviour	
		self.hierarchyoptions = hierarchyoptions		
		self.show_singlefacet_header = show_singlefacet_header		
		self.number_opts = number_opts or {}	
		self.mask = mask	
		self.customvalues = customvalues	
		self.facetvalues = []
		self.explanation = explanation
		self.mptt = mptt  # this is also used in the template to mark the mptt facets!
		self.exclude = self.get_excluded_objs(exclude)
		self.group = group  # the groups the facet is included in
		self.id = id(self)



	def get_excluded_objs(self, exclude_list):
		""" from a list of strings representing the objs we want to exclude, we return a list of the model instances 
		    This is needed in order to avoid encoding problems when checking for equality - the 'self.originalModel.objects.get' 
		    syntax circumvent that... """
		if not exclude_list:
			return []
		else:
			ll = []
			attribute = self.displayAttribute or self.originalAttribute
			for x in exclude_list:	
				querypar = {attribute: x}
				try:
					ll.append(self.originalModel.objects.get(**querypar))	
				except:
					pass		
			# djfacetlog('noise')
			# djfacetlog(str(ll))
			return ll		
		
	#	MAIN CREATION FUNCTION -----------

	def create_allfacetvalues(self): 
		# 
		"""This method should be called only once: it instantiates all the 
			values comprised in this facet, and adds them to it. IDs are generated and stored."""
		
		
		# **case1: 
		if self.customvalues: 
			for x in self.customvalues:
				# rem that in this case the name doesn't match the DB! it's really a label..
				v =	 FacetValue(name=x, facet=self, customvalues=self.customvalues[x], number_opts=self.number_opts, show_singlefacet_header=self.show_singlefacet_header)
				self.add_facetvalue(v)
		
		# **case2:	TODO: THIS HASN'T BEEN REVISED IN A WHILE
		elif self.hierarchyoptions:			
			values_list = self.originalModel.objects.exclude(id__in=[x.id for x in self.exclude]).values_list(self.originalAttribute, flat=True)
			
			if self.hierarchyoptions.get('alpha'):
				# remove duplicates, and make everything uppercase
				lookup_choices = list(set(val[0].upper() for val in values_list if val))
				for x in lookup_choices:
					v =	 FacetValue(name=x, facet=self, hierarchytype='alpha', number_opts=self.number_opts, show_singlefacet_header=self.show_singlefacet_header, mask=self.mask)	# father=0 implied
					self.add_facetvalue(v)
					# TODO: instantiates also the subfacets of 'A', 'B', etc...
					#  for the mom we can do without this
				
			if self.hierarchyoptions.get('range'):
				# from 30, we find min and max available and create [1900-1930, 1930-1960, etc.]
				therange = self.hierarchyoptions['range']
				values_list = sorted(list(set(values_list)))
				if values_list[0] == 0:
					values_list.remove(0)
				themin = findmin(therange, min(values_list))
				themax = findmax(therange, max(values_list))
				rangelist = buildranges(themin, themax, therange) #[('990-1020', (990, 1020))]
				for x in rangelist:
					v =	 FacetValue(name=x[0], facet=self, hierarchytype='range', hierarchyextra=x[1], number_opts=self.number_opts, show_singlefacet_header=self.show_singlefacet_header, mask=self.mask)
					self.add_facetvalue(v)
		
		# **case3:
		# 2010-11-09 : new ==> MPTT models // in this case EXCLUDE doesn't work
		elif self.mptt:
			
			#  HELPER function for the recursive traversing of MPTT tree
			def helper_children( MPTTInstance, afacet, facetValueFather, rootfather):
				# remember: when we pass a father arg, what gets saved is the ID of the father
				newValue =	FacetValue(name=MPTTInstance.name, facet=afacet, 
										father=facetValueFather, rootfather=rootfather, mpttoriginalID=MPTTInstance.id, mptt_treeID=MPTTInstance.tree_id)
				afacet.add_facetvalue(newValue)
				children = MPTTInstance.get_children()
				if children:
					for child in children:
						helper_children(child, afacet, newValue, rootfather)

			# in this case we don't take unique values, but each instance is a facet value
			top_level = self.originalModel.tree.root_nodes()
			for x in top_level:
				newValue =	FacetValue(name=x.name, facet=self, father=None, rootfather=None, mpttoriginalID=x.id, mptt_treeID=x.tree_id)
				self.add_facetvalue(newValue)
				children = x.get_children()
				if children:
					for child in children:
						helper_children(child, self, newValue, newValue)

		
		# **case4:		
		# in this case the originalAttribute is usually a customized field built for query-optimization 
		# while the displayAttribute is the original field that gets displayed	
		elif self.displayAttribute:
			# The values_list is therefore a list of tuples
			values_list = self.originalModel.objects.exclude(id__in=[x.id for x in self.exclude]).values_list(self.originalAttribute, self.displayAttribute)
			# here we assume that the customized originalAttribute has been created with a deterministic function (= subsequent 
			# applications of the function to the same value x always return y [e.g., substr("de ")] ) 
			#  .. so the generated list of tuples can be sorted like this:
			values_list = sorted(list(set(values_list)))
			for x in values_list:
				if not self.get_facetvalue_from_displayname(x[1]):	 #extra check for non-deterministic displayAttribute
					v =	 FacetValue(name=x[0], displayname=x[1], facet=self, number_opts=self.number_opts, show_singlefacet_header=self.show_singlefacet_header, mask=self.mask) # father=0 implied
					self.add_facetvalue(v)
		
		# **case5:
		else:
			# values_list = self.originalModel.objects.values_list(self.originalAttribute, flat=True).annotate(c=Count(self.originalAttribute))
			values_list = self.originalModel.objects.exclude(id__in=[x.id for x in self.exclude]).values(self.originalAttribute).annotate(howmany=Count(self.originalAttribute))
			# values_list = sorted(list(set(values_list)))
			for x in values_list:
				v =	 FacetValue(name=x[self.originalAttribute], facet=self, number_opts=self.number_opts, show_singlefacet_header=self.show_singlefacet_header,  mask=self.mask, howmany=x['howmany']) # father=0 implied
				self.add_facetvalue(v)

	
			
	def add_facetvalue(self, facetvalue):
		"""adds a facet value object"""
		self.facetvalues.append(facetvalue)

	def add_multiplefacetvalues(self, facetvaluelist):
		""" adds a list of facet objects"""
		for i in facetvaluelist:
			self.facetvalues.append(i)

	def remove_facetvalue(self, facetvalue):
		self.facetvalues.remove(facetvalue)



	def remove_all_empty_values(self):
		""" 2010-10-29: added method that removes all the empty values, cause they're not useful in searches! 
			in 'facetsgroup.py'=> 'buildfacets_fromspecs', the REMOVE_EMPTY_VALUES = True triggers this routine
		"""
		for x in self.facetvalues:
			try:
				if x.name == None or x.name == 0 or x.name.strip() == "":
					self.remove_facetvalue(x)
			except:	 # cause some values are numbers I imagine
				pass
		



	# getters:



		# 'behaviour' : [ {'resulttype' : 'people', 
		#				   'querypath' : None,
		#				 'explanation' : "showing all people with selected surname " } ,]

	def get_behaviour(self, resulttype = None, explanation = None):
		if self.behaviour:
			if resulttype and not explanation:
				for b in self.behaviour:
					if b.get('resulttype') == resulttype:
						return b.get('querypath')
				return None
				# raise Exception("Error: wrong resulttype")
			if resulttype and explanation:
				for b in self.behaviour:
					if b.get('resulttype') == resulttype:
						return b.get('explanation')
				return None
				# raise Exception("Error: wrong resulttype [explanation case]")
			else:
				return self.behaviour  # we return the whole list
		raise Exception("Error: no behaviour defined for facet ** %s **" % self.uniquename )


	def get_inversebehaviour(self, resulttype):
		if self.behaviour:
			for b in self.behaviour:
				if b.get('resulttype') == resulttype:
					return b.get('inversepath')
		return None



	def get_facetvalue_from_name(self, name):
		"""returns a FacetValue object from its name"""
		for x in self.facetvalues:
			if x.name == name:
				return x
		return None

	def get_facetvalue_from_displayname(self, name):
		"""returns a FacetValue object from its name"""
		for x in self.facetvalues:
			if x.displayname == name:
				return x
		return None


	def get_facetvalue_from_id(self, valueid):
		"""returns a FacetValue object from its UNIQUE id"""
		if DJF_URL_AS_NUMBERS:
			try:
				valueid = int(valueid)
			except Exception, e:
				djfacetlog("Facet.py>> DJF_URL_AS_NUMBERS is True but can't convert facetvalue ID to int! Error: %s" % (e), True)
		for x in self.facetvalues:
			if x.id == valueid:
				return x
		return None


	def get_facetvalues(self, level=0):
		"""get the facet_values OBJECTS with the specified *father* = a specific level (top level by default)"""
		if level == 'all':
			valuelist = self.facetvalues
		else:
			valuelist = [x for x in self.facetvalues if x.father == level]
		valuelist.sort(key=lambda x: x.displayname)
		return valuelist


	def get_facetvalues_sample(self, level=0, maxnumber=20):
		"""get only a sample of the facet_values OBJECTS - useful for 
		   setting up the interface at the beginning - if the number of values is > than maxnumber
		   the last item is a signal for the template renderer: it'll be creating a link  
		   to the js function that calls 'get_facetvalues' above.
		"""
		if maxnumber == 0:
			maxnumber = 100000000
		if level == 'all':
			valuelist = self.facetvalues
		else:
			valuelist = [x for x in self.facetvalues if x.father == level]
		if len(valuelist) > maxnumber:
			valuelist = valuelist[:maxnumber]
			valuelist.sort(key=lambda x: x.displayname)
			# 99morebutton99 is the string recognized in the template as the more button!
			valuelist.append(FacetValue("99morebutton99", self))
		else:
			valuelist.sort(key=lambda x: x.displayname)
		return valuelist


# =========
# MPTT methods
# =========

	def get_facetvalue_from_MPTTid(self, MPTTid):
		"""returns a FacetValue object from its MPTT id - valid only for MPTT values"""
		for x in self.facetvalues:
			if x.mpttoriginalID == MPTTid:
				return x
		return None



	def get_MPTTroot(self, facetvalue):
		""" 
		2012-05-15
		MPTT ONLY: given an instance, return the root element of its tree
		THis is done without hitting the DB - only based on the Faceted Manager object
		"""

		if not facetvalue.father:
			return facetvalue
		else:
			return self.get_MPTTroot(self.get_facetvalue_from_id(facetvalue.father))
		

	def recursive_tree_forfacetvalue(self, facetvalue):
		""" MPTT ONLY: given an instance, we're outputting the minimal tree that contains all of them
		
			The tree is represented with a list [father, child, child2, child3 etc...]
			The values are represented as facetvalues objects

		 """
		
		if not facetvalue:
			return []
		if not facetvalue.father:
			return [facetvalue]
		father = self.get_facetvalue_from_id(facetvalue.father)
		result = self.recursive_tree_forfacetvalue(father) + [facetvalue]
		return result
	
	

	# NOTE: depends on the function above..
	# 2012-05-22: STILL NEEDED? 
	
	def recursive_tree_forfacetvalue_list(self, facetvalue_list):
		""" MPTT ONLY: given a list of instances, we're outputting the minimal tree that contains all of them
		
			The tree is represented with a dict {parent: [children]} where each element gets to be a key only if it's a parent
				(the parent is the ID of the value, the children the values themselves)

		 """
	
		# ======  second implementation [works, but no counts are maintained, so after we return the results 
		# we've got to make sure the right facetvalue instances are taken (= the ones with the update howmany 
		# parameter.... check the 'tree_visualizer' function in djf_tags.py) ]:
		d = {}
		for x in facetvalue_list:
			tree_list = self.recursive_tree_forfacetvalue(x)
			for x in tree_list:
				par = x.father  # it's the ID number, not the object
				child = x.id  # the fv instance
				try:
					if not child in d[par]:
						d[par].append(child)
				except:
					d[par]=[child]
		return d
		
			
		



