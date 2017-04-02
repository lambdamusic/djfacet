from djfacet.constants import *
from djfacet.facet import *
from fb_utils.utils import djfacetlog




#
# FacetsGroup : abstracts the collective entity composed by multiple facets
#



class FacetsGroup(object):
	""" Class representing an arbitrary group of facets 
		=+=
		uniquename: name used for identification purposes
		label: display label
		position: ordering info
		facets: the list of facets contained
		facets_specs: list of lists containing the specs for the facets (see facetspecs.py) 
		=+=
	
	"""
	
	def __init__(self, uniquename, label, position = 1, facets_specs = None, bkcolor="FFFFFF"):
		self.uniquename = uniquename
		self.label = label
		self.position = position
		self.bkcolor = bkcolor
		# self.informationspace = informationspace
		if facets_specs:
			self.facets = []
			self.buildfacets_fromspecs(facets_specs)
		else:
			self.facets = []
		
	# MAIN CREATOR FUNCTION!
		
	def buildfacets_fromspecs(self, facetspecs, REMOVE_EMPTY_VALUES = True):
		"""Creates facets objects from a list of dictionaries specifying how the facets are defined, 
			using 'grouping' to find out which are the right facets to explode e.g.:
			[{	'label' : 'surname' , 
				'model' : Person , 
				'grouping' : "group_one", }, .... ]
				
			REMOVE_EMPTY_VALUES: defaults to true, makes sure we move all empty values from facets!	
			If we set it to False, the FB works but there's a bug with the cache... TODO
			
			2012-05-22: added 'active' to facetspecs definition - quick way to deactive a facet - defaults to True. 
			
			
		"""				
		for i in facetspecs:
			if self.uniquename in i['appearance']['grouping'] and i.get("active", True):
				
				model = i.get('model')  # required
				uniquename = i.get('uniquename') # required
				mptt = i.get('mptt', False)
				explanation = i.get('explanation', "")
				appearance_specs = i['appearance']
				mask = appearance_specs.get('mask', None)
				customvalues = appearance_specs.get('customvalues', None)
				dbfield = appearance_specs.get('dbfield', None)
				displayfield = appearance_specs.get('displayfield', None)
				hierarchyoptions = appearance_specs.get('hierarchy', None) # ... or the hierarchy opts
				show_singlefacet_header = appearance_specs.get('show_singlefacet_header', True)
				number_opts = appearance_specs.get('number_opts', None) 				
				ordering = appearance_specs.get('ordering', None) 				
				exclude = appearance_specs.get('exclude', False)
				
				behaviour = i.get('behaviour', None) # behavior of each facet//result_type
				group = self
				# Facet(name, originalModel, originalAttribute, displayAttribute = None, behaviour = None, hierarchyoptions= None,  mask=None, customvalues = None, mptt = False, exclude=False, group=[])
				djfacetlog("..adding facet: %s" % uniquename, True)
				x = Facet(uniquename, appearance_specs['label'], model, 
								dbfield, displayfield, ordering, behaviour, hierarchyoptions, number_opts, mask, customvalues, mptt, explanation, group=group, show_singlefacet_header=show_singlefacet_header)
							
				self.facets.append(x)
				# also instantiates all the values!
				x.create_allfacetvalues()

				if REMOVE_EMPTY_VALUES:  # by default yes
					x.remove_all_empty_values()
			

	def add_facet(self, facet):
		"""adds a facet object"""
		self.facets.append(facet)

	def add_multiplefacets(self, facetlist):
		""" adds a list of facet objects"""
		for i in facetlist:
			self.facets.append(i)
		
	def remove_facet(self, facet):
		self.facets.remove(facet)
		
		
	def get_facet_from_name(self, name):
		"""returns a Facet object from its name"""
		for x in self.facets:
			if x.name == name:
				return x
		return None		

	def get_facet_from_id(self, id):
		"""returns a Facet object from its ID"""
		for x in self.facets:
			if x.id == id:
				return x
		return None

	def get_facetvalue_from_id(self, valueid):
		"""returns a FacetValue object from its id"""
		for x in self.facets:
			r = x.get_facetvalue_from_id(valueid)
			if r:
				return r
		return None
		
