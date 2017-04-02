
from django.db.models.base import ModelBase
from django.db.models.query import QuerySet
from django.db.models import Avg, Max, Min, Count, Q
import operator, copy

from fb_utils.utils import *

from djfacet.constants import *


##################
#  Wed Aug	4 17:32:49 BST 2010
# QueryHelper:
#
##################





class QueryHelper(object):
	""" The QueryHelper object contains all the methods needed for updating the FacetValues Count.
		It inspects the facetspecs dictionary and builds a reversed-path from the result type to the facet infospace, 
		so to craete a count query based on current parameters.
		
		This method is used only by the *refresh_facetvalues* method in facetedmanager. 
	
		Properties:
			<facet>: the facet whose values we are looking for
			<resulttypeName>: the result type for this search
			<resulttypeModel>: extracted from resulttypeName, for practicality
			<activeIDs>: precalculated list of object IDs, essential for running this method.  
			<queryargs>: the list of facetvalues in the current query. Used only by the MPTT routine.
			<limit>: number representing how many values to return (eg for sampling purposes)
	"""

	def __init__(self, resulttypeName, facet, activeIDs, queryargs=None, limit=1000000000000000, showonly_subs=False):
		self.facet = facet
		self.resulttypeName = resulttypeName
		self.activeIDs = activeIDs
		self.queryargs = queryargs	
		self.resulttypeModel = self.get_resulttype_from_name(resulttypeName)['infospace'] # so that it's called only once..
		self.limit = limit or 1000000000000000	# if None or 0 is passed, default to unlimited
		self.showonly_subs = showonly_subs
		self.TOTCURRENT_RESULTS = 0
		if activeIDs:
			self.TOTCURRENT_RESULTS = len(activeIDs) # 2012-04-26: used to remove searchvalues that have no filtering potential

	def should_we_use_distinct(self, facetModel, resultModel):
		""" Returns false is the two models are different (proxy models don't count)
			We found out that if they are the same the 'Count' query does not need the 'distinct' directive
			.... [2010-10-28]
		 """
		if facetModel._meta.proxy:
			facetModel = facetModel._meta.proxy_for_model
		if resultModel._meta.proxy:
			resultModel = resultModel._meta.proxy_for_model		

		if facetModel == resultModel:
			djfacetlog(".... Detected exception: *facetModel == resultModel*  ==> no need to use *distinct* in Count query")
			return False
		return True


	def get_resulttype_from_name(self, name):
		"""Duplicate method in FacetedManager: we put it also here so that QueryHelper is autonomous 
		......get the result_type dictionary from the name """
		# from SPECS import result_types as all_result_types
		for i in DJF_SPECS.result_types:
			if i['uniquename'] == name:
				return i
		return None

	def getBehaviourTuple(self):
		""" extract the behaviour(s) of a facet (given a specific resultType), and puts them into a nice tuple. 
		In the case of multuple behaviours, that is because we have OR queries.. """

		resulttypeName, facet = self.resulttypeName, self.facet
		if not facet.behaviour:
			return None

		paths_tuple = None			
		existing_path = facet.get_behaviour(resulttypeName)
		if existing_path:
			# this is the case with one statement (which becomes an AND in the aggregated query)
			if type(existing_path) == type("a string"):
				paths_tuple = (existing_path,)
			# this is the case with OR statements
			elif type(existing_path) == type(('a tuple',)):					
				paths_tuple = existing_path 
			return paths_tuple
			
	
		# ========
		# METHODS FOR CALCULATING A QUERYPATH
		# ========


	def _calcReversedPath(self, explodedPath):
		# PLEASE explain the line below - otherwise you'll forget! ++++
		newpath = "__".join([explodedPath[k]['inversePath'] for k in sorted(explodedPath.iterkeys(), reverse=True) if explodedPath[k]['toModel'] is not None])
				# newpath = newpath + "__id__in"				
				# case when startmodel and endmodel are the same, 
				# eg a facet is just a text field on the same model we are querying (= the result type)
				# if newpath == "__id__in":
				#	newpath = "id__in"
		return newpath



	def getExplodedPaths(self):
		""" From the current instance of QueryHelper(resType, Facet, ActiveIds)
		 ==> returns the whole exploded path(s) based on the behaviours of the Facet for that resType. 
		The result is a list of explodedPaths..

		EG of exploded queryPath:
		[{1: {'path': 'record', 'inversePath': 'event', 'type': 'RelatedObject', 
			'toModel': <class 'ltb.ltbapp.models.Record'>, 'fromModel': <class 'ltb.ltbapp.models.Event'>}, 
		2: {'path': 'transcription', 'inversePath': 'transcr_inrec', 'type': 'ForeignKey', 
			'toModel': <class 'ltb.ltbapp.models.Document'>, 'fromModel': <class 'ltb.ltbapp.models.Record'>}, 
		3: {'path': 'doc_type', 'inversePath': 'documents', 'type': 'ManyToManyField', 
			'toModel': <class 'ltb.ltbapp.models_authlists.DocumentType'>, 'fromModel': <class 'ltb.ltbapp.models.Document'>}}, 
		{..another path..}]

		"""
		resulttypeModel = self.resulttypeModel
		paths_tuple = self.getBehaviourTuple()
		djfacetlog("ORIGINALBEHAVIOUR = %s" % str(paths_tuple))
		alist = []

		if paths_tuple:
			for path in paths_tuple:
				alist.append((self.inspectQuery(resulttypeModel, path)))
			return alist




	def inspectFieldInfo(self, aModel, aFieldName):
		""" Tells you information of a model's field. 
			
			Particularly useful for KEYS: shows how two Django models are connected..	 
			Given a model, and the field name represeting its KEY, it returns a dict,  for example:		
			{'path': 'record', 'inversePath': 'event', 'type': 'RelatedObject', 
				'toModel': <class 'ltb.ltbapp.models.Record'>, 'fromModel': <class 'ltb.ltbapp.models.Event'>}
		"""

		from django.db.models.fields import FieldDoesNotExist
		try:
			field = aModel._meta.get_field_by_name(aFieldName)[0]
		except FieldDoesNotExist:
			raise Exception, "Field not existing : [%s]" % aFieldName

		if type(field).__name__ == 'RelatedObject':
			return {'fromModel' : aModel, 'path': aFieldName, 'toModel' : field.model, 'inversePath' : field.field.name, 'type' :  type(field).__name__ }
		elif type(field).__name__ == 'ForeignKey':
			return {'fromModel' : aModel, 'path': aFieldName, 'toModel' : field.related.parent_model, 'inversePath' : field.related_query_name(), 'type' :	type(field).__name__ }
			# return [aModel, aFieldName, field.related_query_name(), field.related.parent_model, type(field).__name__ , field]
		elif type(field).__name__ == 'ManyToManyField':
			return {'fromModel' : aModel, 'path': aFieldName, 'toModel' : field.related.parent_model, 'inversePath' : field.related_query_name(), 'type' :	type(field).__name__ }
			# return [aModel, aFieldName, field.related_query_name(), field.related.parent_model, type(field).__name__ , field]
		else:  # NORMAL FIELD: recognizable by the fact that toMolde = None!
			return {'fromModel' : aModel, 'path': aFieldName, 'toModel' : None, 'inversePath' : None, 'type' :	type(field).__name__ }			
			# djfacetlog("inspectFieldInfo: [[%s] %s] is not a KEY field, but a %s" % (str(aModel), str(aFieldName), field.get_internal_type()))
			# return None



	def inspectQuery(self, startmodel, querystring):
		""" Helper method:
			From a model and a query-path, by using the 'inspectFieldInfo' above, we return a list of 
			model objects and methods that break down all the query, EG:

			>>> q.inspectQuery(Event, 'record__transcription__doc_type__name')
			{1: {'path': 'record', 'inversePath': 'event', 'type': 'RelatedObject', 
				'toModel': <class 'ltb.ltbapp.models.Record'>, 'fromModel': <class 'ltb.ltbapp.models.Event'>}, 
			2: {'path': 'transcription', 'inversePath': 'transcr_inrec', 'type': 'ForeignKey', 
				'toModel': <class 'ltb.ltbapp.models.Document'>, 'fromModel': <class 'ltb.ltbapp.models.Record'>}, 
			3: {'path': 'doc_type', 'inversePath': 'documents', 'type': 'ManyToManyField', 
				'toModel': <class 'ltb.ltbapp.models_authlists.DocumentType'>, 'fromModel': <class 'ltb.ltbapp.models.Document'>}}

				+++ add that we include info about the latest field too!!! ++++

		"""
		exit = {}
		n = 0	# to order the result
		tempmodel = startmodel
		elements = querystring.split("__")

		for el in elements:
			if tempmodel:
				# djfacetlog("el: %s, model: %s" % (el, tempmodel))
				res = self.inspectFieldInfo(tempmodel, el)
				if res:	 # = if the field represents a KEY
					n += 1
					exit[n] = res
					tempmodel = res['toModel']
				else:
					break	# CHANGE: meaning that if the querystring doesn't produce KEYS, we return nothing
		return exit




	# ========
	# METHODS FOR EXTRACTING AVAILABLE FACETVALUES
	# ========
			

	def calculate_facetvalues(self, valuesbatch = None):  
		""" returns a list of FacetValue objects with updated counts
			.. it's a wrapper for the '__calcvalues' method.....
			
			VALUESBATCH: it is used only by cacheDB, *only* for the old algorithm, to avoid memory crashes
				TODO: eliminate? still required?

		"""
		
		# various cases, depending on whether the reversedBehaviour has been defined manually or not.
		facet , resulttypeName = self.facet , self.resulttypeName
		inverseBehaviour = facet.get_inversebehaviour(resulttypeName)
		djfacetlog("\n+++++\nREFRESH Facet Values: Facet= *%s*	 Result= *%s* \n+++++" % (str(facet.uniquename), str(resulttypeName)))
		if inverseBehaviour: 
			if type(inverseBehaviour) == type({}):
				if inverseBehaviour.get('GENERIC-FIELD'):
					return self._calcvalues(parameter='GENERIC-FIELD', valuesbatch = valuesbatch)
			elif type(inverseBehaviour) == type(('a tuple',)):
				return self._calcvalues(inverseBehaviour=inverseBehaviour, valuesbatch = valuesbatch)
			elif type(inverseBehaviour) == type("a string"):
				return self._calcvalues(inverseBehaviour=(inverseBehaviour,), valuesbatch = valuesbatch)
		else:
			return self._calcvalues(valuesbatch = valuesbatch)





	def _calcvalues(self, parameter = None, inverseBehaviour = None , valuesbatch = None):
		"""Inner method that computes the available facetvalues"""
		# SET UP VARIABLES	
		resulttypeName, facet, activeIDs = self.resulttypeName, self.facet, self.activeIDs
		resulttypeModel = self.resulttypeModel
		dbfield = facet.originalAttribute

		if parameter == "GENERIC-FIELD":
			# in this case, we have an attribute that applies to all models (cf.'revision' or 'edited record' facets in LTB)
			facetModel = resulttypeModel
		else:
			facetModel = facet.originalModel
		# 2010-08-20: COMMENTED OUT WHAT FOLLOWS... will LTB WORK ? ? ? ? NEED TO TEST
		# CAUSE I DONT SEE ANY REASON WHY IT SHOULDN'T....
		# if facetModel._meta.proxy:	# with Proxy models queries seem to break
		#	facetModel = facetModel._meta.proxy_for_model

		# CALCULATE INVERSE BEHAVIOUR, IF NOT PROVIDED
		if inverseBehaviour:
			djfacetlog("Found INVERSEBEHAVIOUR = %s" % str(inverseBehaviour))
			reversed_paths_list=[]
			for path in inverseBehaviour:
				reversed_paths_list.append(path)					
		else:		
			explodedPathList = self.getExplodedPaths()
			djfacetlog("Calculated EXPLODEDPATHLIST = %s" % str(explodedPathList))
			# extract the reversed query_strings...
			# mind that even if explodedPathList is empty, that is =[{}], the iteration runs one time anyways!
			# this is the case when a facet is just a text field on the same model we are querying
			reversed_paths_list=[]
			for expl_path in explodedPathList:
				reversed_paths_list.append(self._calcReversedPath(expl_path))

		djfacetlog("...RUNNING Query USING VALUES:\n**FacetModel: %s\n**ReverseQuerypaths: %s\n**DbField: %s\n**ResultTypeModel :%s" % (facetModel, 
				str(reversed_paths_list), dbfield, str(resulttypeModel)))

		
		# **** in this case we have a sequence of ORs... we didn't find a way to use Count so I apply the old algorithm
		if len(reversed_paths_list) > 1:
			return self._calcvaluesForORQueries(reversed_paths_list, facetModel)
		# **** in this case there are no ORs in the specs definition, so we can use Django's annotate function (=Count)
		else:
			if reversed_paths_list[0]: 
				count_argument = reversed_paths_list[0]
			else: # *** if there's a case with GENERIC FIELDS, the count_argument is the same as dbfield
				count_argument = dbfield
			return self._calcvaluesForStandardQueries(reversed_paths_list[0], count_argument, facetModel)




	def _calcvaluesForStandardQueries(self, reversed_path, count_argument, facetModel):
		"""
		Routine for calculating the facetvalues

		eg: Gender.objects.filter(person__id__in=range(1000, 2000)).values('name').annotate(Count('person', distinct=True))
		
		We count the number of results in the current query and store the number in TOTCURRENT_RESULTS variable. 
		This way we can immediately remove filter options that can't be used (ie they are not < TOTCURRENT_RESULTS). 
		In other words, all new filters must always supports 'zoom-in' operations. 
		
		In the case of MPTT facets, if inheritance is calculated on the fly (DJF_MPTT_INHERITANCE=True), we can't 
		prune the resultset based on TOTCURRENT_RESULTS, because values with res 0 may have sub-values that have results.
		What we do in this case is:
		...if no queryargs: 
				- use filter(level=0) for selecting only top level mptt instances
		...if queryargs:
				- get all the values, and then prune the resultSet via the _validateMPTTvalue routine; take top level
				 mptt values only, or children in the the case one of the queryargs is an mptt values 
			
		
		If DJF_MPTT_INHERITANCE is False, since all inherited properties for tree-elements have been stored (exploded) 
		at DB level, we just get the facetvalues the normal way, using the TOTCURRENT_RESULTS trick.
		
		"""
		resulttypeName, facet, activeIDs, queryargs, LIMIT = self.resulttypeName, self.facet, self.activeIDs, self.queryargs, self.limit
		if not queryargs:  #prevent error when caching from console
			queryargs = []
		resulttypeModel = self.resulttypeModel
		dbfield = facet.originalAttribute
		tot_allvalues = False # used to store info on the tot number of fvalues, irrespectively of the limit

		# ===
		# launch a query to find all possible values
		
		all_values, valid_values = self._setupQuerySet(reversed_path, facetModel, count_argument)	
		counter, tot_limitvalues, remaining_values, output = 0, 0, 0, []
		tot_allvalues = len(all_values)
		
		djfacetlog("____________ ==> got the possible facet values _____________ tot: %d (limit=%s / MPTT=%s)\n" % (len(valid_values), 
																											str(LIMIT), str(facet.mptt)))
		# ===
		# for each value, UPDATE THE FV OBJECTS
				
		for value in valid_values:
			
			# IF MPTT AND DJF_MPTT_INHERITANCE
				
			if facet.mptt and DJF_MPTT_INHERITANCE:	 # => flags that mptt inheritance values have to be calc on the fly
			
				fv = facet.get_facetvalue_from_MPTTid(value['id'])
				
				fv = self._validateMPTTvalue(facet, fv, queryargs, current_output = output)
				
				if fv and (fv.id not in [x.id for x in queryargs]):  #make sure we dont' show previously selected filters
					counter += 1				
						
					if tot_limitvalues <= LIMIT: 
						subs, howmany = self._calcMPTT_inheritance(facet, fv, all_values, dbfield, DJF_MPTT_INHERITANCE)
						# if howmany > 0 and howmany != self.TOTCURRENT_RESULTS:				
						if howmany > 0 and howmany <= self.TOTCURRENT_RESULTS:				
							fv_copy = copy.copy(fv)	 #make a copy, so we don't update the static FM object
							fv_copy.howmany = howmany
							fv_copy.subspreview = subs
							tot_limitvalues += 1
							output.append(fv_copy)							
							try:  #sometimes this fails due to ascii encoding errors, so we're catching it
								djfacetlog("===>> updating FV count (with inference) for value: *%s=%s* (validated as %s) ==> +%d+	[%d of %d]" %
								 (str(value), facet.get_facetvalue_from_MPTTid(value['id']).name, fv.name, howmany, counter,  len(valid_values)))
							except:
								pass						
	
				else:
					tot_allvalues -= 1
					try:
						pass # if you want to debug this comment this line
						djfacetlog("===>> NOT VALIDATED: *%s=%s* [%d of %d]" % (str(value), facet.get_facetvalue_from_MPTTid(value['id']).name,	counter,  len(valid_values)))  
					except:
						pass
		
		
			# IF normal value - or MPTT but NOT DJF_MPTT_INHERITANCE
			
			else:
				fv = facet.get_facetvalue_from_name(value[dbfield])
				if fv and value['count'] and (fv.id not in [x.id for x in queryargs]):
					counter += 1
					try:  
						djfacetlog("===>> updating FV count for value: *%s* ==> +%d+	[%d of %d]" % (str(value[dbfield]), 
																				value['count'], counter,  len(valid_values)))
					except:
						pass
					fv_copy = copy.copy(fv) 
					fv_copy.howmany = value['count']
					if facet.mptt:
						# fv_copy.subspreview = self._calcMPTT_subsPreview(facet, fv, all_values, dbfield)
						fv_copy.subspreview = self._calcMPTT_inheritance(facet, fv, all_values, dbfield, DJF_MPTT_INHERITANCE)
					tot_limitvalues += 1
					output.append(fv_copy)
				else:
					# update the count of tot available values
					tot_allvalues -= 1
					try:
						pass # if you want to debug this comment this line
						djfacetlog("===>> NOT VALIDATED: *%s* ==> +%d+	[%d of %d]" % (str(value[dbfield]), 
												value['count'], counter,  len(valid_values)))  
					except:
						pass								
			
		
		remaining_values = tot_allvalues - tot_limitvalues
		for fv_copy in output:
			fv_copy.tot_left = remaining_values
			fv_copy.tot_inbatch = tot_limitvalues
			fv_copy.tot_all = tot_allvalues
					
		if facet.exclude:  # this is just to flag it up: the real exclusion happens at FM loading time (see facet.py)
			djfacetlog("=====>> ****** Mind that we're excluding values found in facet.exclude: %s" % str(facet.exclude))
		return output





	def modify_countarg_forMPTT(self, facet, count_argument):
		# print "\n******\ncount_argument= ", count_argument, " facet.originalAttribute=", facet.originalAttribute, "\n******"
		if facet.originalAttribute:
			if count_argument.endswith(facet.originalAttribute):
				count_argument = count_argument.rstrip(facet.originalAttribute)
		# print "\n******\ncount_argument= ", count_argument, "\n******"
		if count_argument:
			count_argument_and_id = count_argument + "__id"
		else:
			count_argument_and_id = "id"
		# print "\n******count_argument_and_id= ", count_argument_and_id, "\n******"
		return count_argument_and_id



	def _validateMPTTvalue(self, mpttfacet, mpttfacetvalue, queryargs, current_output):
		"""
		Method that checks if a MPTT facetvalue should be returned, based on current query parameters.
		Mind that this happend without considering counts, but based only on the fact that values are direct children, top level
		ones or siblings of what is already selected. 

		<self.showonly_subs> Fvalue_ID indicating that we're digging into a specific tree, so non-tree values are discarded.
		<current_output> List of already validate MPTT values, used for checking against duplicates.
		
		Eg: if these are the contents of an imaginary 'Religion name' facet:		
		
		A: religion_catholic
		B: ---religion_catholicbritish
		C: ------religion_catholicscottish
		D: religion_taoism
		E: ---religion_chinesetaoism
		F: ---religion_japtaoism
		G: ------religion_tokyotaoism
				
		If the query contains no args, A and D are returned. 
		If the query contains A, B and D are returned.
		If the query contains B and D, C and E and F are returned, etc...
				
		"""
		
		if self.showonly_subs:
			# djfacetlog("noise")
			fv = mpttfacet.get_facetvalue_from_id(self.showonly_subs)
			if fv.id == mpttfacetvalue.father:
				# djfacetlog("noise")
				return mpttfacetvalue
		elif queryargs:
			
			# TODO: understand this routine better!
			
			for fv in queryargs:
				# if it is a direct subconcept of current queryargs, fine
				if mpttfacetvalue.father == fv.id:
					djfacetlog("..Item +%s+ is a good candidate cause it's a subconcept of queryarg *%s*" % (mpttfacetvalue.name, fv.name))
					return mpttfacetvalue
				# if an element is from another tree, return it at the top level (=0)
				elif (fv.mptt_treeID != mpttfacetvalue.mptt_treeID):					
					root_value = mpttfacet.get_MPTTroot(mpttfacetvalue)
					if root_value.id not in [x.id for x in current_output]:
						djfacetlog("..Item +%s+ is a good candidate cause it's from a different mptt tree than queryargs: %d" % (mpttfacetvalue.name, mpttfacetvalue.mptt_treeID))
						return root_value
				elif (fv.father == mpttfacetvalue.father):
					djfacetlog("..Item +%s+ is a good candidate cause it's a sibling of: %s" % (mpttfacetvalue.name, fv.name))
					return mpttfacetvalue
				# if an element is from the same tree, return the highest father they do not have in common..
				elif (fv.mptt_treeID == mpttfacetvalue.mptt_treeID):
					tree1 = mpttfacet.recursive_tree_forfacetvalue(fv) # the tree of the pre-selected arg
					if mpttfacetvalue.id not in [x.id for x in tree1]:
						tree2 = mpttfacet.recursive_tree_forfacetvalue(mpttfacetvalue) # the tree to test
						# print "\n", [x.name for x in tree1], "\n", [x.name for x in tree2]
						for n in range(len(tree1)):
							if (tree1[n] != tree2[n]) and (tree2[n].id not in [x.id for x in current_output]):
								# print "\n\n", [x.id for x in current_output], "\n"
								djfacetlog("..Item +%s+ is a good candidate cause it's from the same mptt tree [%d] but different branch. Highest father that is NOT in common is *%s*" % (mpttfacetvalue.name, mpttfacetvalue.mptt_treeID, tree2[n].name))
								return tree2[n]
				else:
					# print "/n/nHERE 3 /n/n"
					return False
		else:
			# only top level mpttvalues are accepted when there are no queryargs
			if mpttfacetvalue.father:
				djfacetlog("..Item +%s+ is Not a good candidate cause it's not at level 0: father= %d" % (mpttfacetvalue.name, mpttfacetvalue.father))
				return False
			else:
				return mpttfacetvalue			
			

	
	def _calcMPTT_inheritance(self, facet, facetvalue, all_values, dbfield, DJF_MPTT_INHERITANCE):
		""" 
		Returns a tuple of lists or a single list depending on whether the MPTT_INHERITANCE is calculated.   
		
		If DJF_MPTT_INHERITANCE = False:
			Get descendants from MPTT, and choose the ones already available in all_values.
			All_values is  
			[{'count': 0, 'name': u'Muslim'}, {'count': 62, 'name': u'Muslim -Shia and Sunni-'}, etc.....]
		
		If DJF_MPTT_INHERITANCE = True:
		
			In this case all_values is like this:
		
			{31L: [104L, 155L, 216L, 45L,], 32L: [212L, 110L,], 33L: [2L, 197L, 186L, 147L, 14L, 221L, 14.... etc.....}
				
			A consolidated dict of mptt-IDs with [list of IDs] of valid results. This would let us do some ad hoc counting.
		
			Approach:
			From current facetvalue, extract corresponding MPTT instance, and get its descendants via DB. 
			If descendants exist in all_values, append relevant [list of IDs] to an output list, and eventually remove duplicates from it. 
		
			That is returned together with a preview-list of the (valid) children of the fvalue, so to be used in a tooltip ...

		"""
		if DJF_MPTT_INHERITANCE:
			mpttinstance = facet.originalModel.objects.get(pk=facetvalue.mpttoriginalID)
			descendants = mpttinstance.get_descendants(True) # includes this element too (MPTT method)
			count_list = []
			subsPreview_list = []
			for mpttval in descendants:
				if all_values.get(mpttval.id):
					count_list += all_values.get(mpttval.id)
					if len(subsPreview_list) < 10 and mpttinstance.id != mpttval.id: #do not include the top level father
						subsPreview_list.append(facet.get_facetvalue_from_MPTTid(mpttval.id))
			return (subsPreview_list, len(set(count_list)))

		else:
			# TODO : to be tested!!!
			subsPreview_list = []
			tree = facet.recursive_tree_forfacetvalue(facetvalue)
			for eachtree in tree:
				for v in all_values:
					if eachtree.name == v[dbfield]:
						subsPreview_list.append(eachtree)
			return subsPreview_list		








	def _setupQuerySet(self, reversed_path, facetModel, count_argument):
		"""
		Called from '_calcvaluesForStandardQueries'
		Separates the logic that selects how to compose the first querySet, based on type of query
		Eg:
		Religion.objects.values('name').annotate(count=Count('country', distinct=True))
		Returns
		 [{'count': 0, 'name': u'Muslim'}, {'count': 62, 'name': u'Muslim -Shia and Sunni-'}, {'count': 9, 'name': u'Shia Muslim'}, {'count': 23, 'name': u'Sunni Muslim'},etc.....]
		"""
		resulttypeName, facet, activeIDs, queryargs, LIMIT = self.resulttypeName, self.facet, self.activeIDs, self.queryargs, self.limit
		resulttypeModel = self.resulttypeModel
		dbfield = facet.originalAttribute
		DISTINCT = self.should_we_use_distinct(facetModel, resulttypeModel)

		# ===
		# 1) IN THIS CASE WE HAVE NO ARGS
		# ===

		if (not queryargs) and (not resulttypeModel._meta.proxy):

			if facet.mptt:	
				if DJF_MPTT_INHERITANCE:			

					# note that in this case we cannot count using the usual 'dbfield' - because two entities existing at different levels/trees in the 
					# hierarchy do not have to be treated as the same. So we use the MPTT id as the fields that gives uniqueness to a facetvalue

					count_argument_and_id = self.modify_countarg_forMPTT(facet, count_argument)
					unique_identifier = 'id'					
					# no need to find counts, just names for now:
					if self.showonly_subs:	# in this case we want to retrieve all results, as they will be filtered later in <_calcMPTT_inheritance>
						valid_values = facetModel.objects.values(unique_identifier,).distinct()
					else:
						valid_values = facetModel.objects.filter(level=0).values(unique_identifier,).distinct()

					# Create all_values with all IDs of valid results, so that we can do the counting later, eg:
					# >>> Religion.objects.values('id', 'country__id')
					# [{'country__id': None, 'id': 360L}, {'country__id': 225L, 'id': 58L}, {'country__id': 193L, 'id': 58L}, 
					#	{'country__id': 137L, 'id': 58L}, {'country__id': 14L, 'id': 58L}, '...(remaining elements truncated)...']					
					all_values = facetModel.objects.values(unique_identifier, count_argument_and_id)

					# here we consolidate the list of dicts above into a simple dict where IDs are grouped
					# {[53L]: [53L], [54L]: [148L, 9L], [55L]: [152L], u[56L]: [101L, 171L, 132L, 121L] , .... }
					dicttemp = {}
					for x in all_values:
						if x[count_argument_and_id]:
							if dicttemp.get(x[unique_identifier]):							
								dicttemp[x[unique_identifier]] += [x[count_argument_and_id]]
							else:
								dicttemp[x[unique_identifier]] = [x[count_argument_and_id]]
					# finally..
					all_values = dicttemp




				else:
					# if DJF_MPTT_INHERITANCE is False	(= counts are final, no need to check inheritance info)
		 				# values have this form:
		 					# [{'count': 0, 'name': u'Muslim'}, {'count': 62, 'name': u'Muslim -Shia and Sunni-'}, {'count': 9, 'name': u'Shia Muslim'}, {'count': 23, 'name': u'Sunni Muslim'},etc.....]
						# TODO: when checking with POMS - maybe we need to force DISTINCT = True here?

					all_values = facetModel.objects.values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).filter(count__lte=self.TOTCURRENT_RESULTS)			

					if self.showonly_subs:
						if facet.ordering:
							valid_values = facetModel.objects.values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).filter(count__lte=self.TOTCURRENT_RESULTS).order_by(facet.ordering)[:LIMIT]
						else:
							valid_values = facetModel.objects.values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).filter(count__lte=self.TOTCURRENT_RESULTS)[:LIMIT]
					else:
						if facet.ordering:
							valid_values = facetModel.objects.filter(level=0).values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).filter(count__lte=self.TOTCURRENT_RESULTS).order_by(facet.ordering)[:LIMIT]
						else:
							valid_values = facetModel.objects.filter(level=0).values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).filter(count__lte=self.TOTCURRENT_RESULTS)[:LIMIT]



			#
			# no Args, no MPTT				
			#
			
			else:	

				all_values = facetModel.objects.values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).filter(count__lte=self.TOTCURRENT_RESULTS)			

				if facet.ordering:
					valid_values = facetModel.objects.values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).filter(count__lte=self.TOTCURRENT_RESULTS).order_by(facet.ordering)[:LIMIT]
				else:
					valid_values = facetModel.objects.values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).filter(count__lte=self.TOTCURRENT_RESULTS)[:LIMIT]



		# ===
		# 2) IF HAVE ARGS, OR THE ARGS ARE HIDDEN VIA A PROXY MODEL
		# ===

		else:
			if resulttypeModel._meta.proxy:
				djfacetlog("... you're using a PROXY MODEL as a results type  ==> I'm adding that implicit behaviour to the query......")
				activeIDs = list(set(activeIDs).intersection(set([x.id for x in resulttypeModel.objects.all()])))
			temp = {}
			if reversed_path:
				temp[reversed_path + "__id__in"] = activeIDs
			else:  # if path is '' or null
				temp["id__in"] = activeIDs

			if facet.mptt: 
				if DJF_MPTT_INHERITANCE:
					# Args and MPTT without pre-calculated counts

					count_argument_and_id = self.modify_countarg_forMPTT(facet, count_argument)
					unique_identifier = 'id'					
					# no need to find counts, just names for now:												
					valid_values = facetModel.objects.filter(**temp).values(unique_identifier).distinct()

					all_values = facetModel.objects.filter(**temp).values(unique_identifier, count_argument_and_id)					
					# here we consolidate the list of dicts above into a simple dict where IDs are grouped
					# {[53L]: [53L], [54L]: [148L, 9L], [55L]: [152L], u[56L]: [101L, 171L, 132L, 121L] , .... }
					dicttemp = {}
					for x in all_values:
						if x[count_argument_and_id]:
							if dicttemp.get(x[unique_identifier]):							
								dicttemp[x[unique_identifier]] += [x[count_argument_and_id]]
							else:
								dicttemp[x[unique_identifier]] = [x[count_argument_and_id]]
					all_values = dicttemp


				else:		
				# TO CHECK in poms: 2012-05-11
					all_values = facetModel.objects.filter(**temp).values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT))			

					if facet.ordering:
						valid_values = facetModel.objects.filter(**temp).values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).order_by(facet.ordering)[:LIMIT]
					else:
						valid_values = facetModel.objects.filter(**temp).values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT))[:LIMIT]	


			else:	

				# Args, no MPTT

				all_values = facetModel.objects.filter(**temp).values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).filter(count__lte=self.TOTCURRENT_RESULTS)			

				if facet.ordering:
					valid_values = facetModel.objects.filter(**temp).values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).filter(count__lte=self.TOTCURRENT_RESULTS).order_by(facet.ordering)[:LIMIT]
				else:
					valid_values = facetModel.objects.filter(**temp).values(dbfield).annotate(count=Count(count_argument, distinct=DISTINCT)).filter(count__lte=self.TOTCURRENT_RESULTS)[:LIMIT]


		# ------------------TO DO -----------------------

		if facet.hierarchyoptions:	
			if facet.hierarchyoptions.get('alpha'):
				pass	#	THIS BIT IS NOT IMPLEMENTED YET
			# if facet.hierarchyoptions.get('alpha'):
			#	valid_values = facetModel.objects.filter(or_args).values(dbfield)
			#	# extract initials, remove duplicates, and make everything uppercase
			#	lookup_choices = list(set([val[dbfield][0].upper() for val in valid_values if val[dbfield]]))
			#	# now just a trick to reformat the list of dicts as in the other cases....
			#	valid_values = [{dbfield : x} for x in lookup_choices]

			if facet.hierarchyoptions.get('range'):
				pass  # NOT IMPLEMENTED YET
				# eg from 30, we find min and max available and create [1900-1930, 1930-1960, etc.]
				# therange = facet.hierarchyoptions['range']
				# values_list = sorted([val[dbfield] for val in valid_values if val[dbfield]])
				# if values_list[0] == 0:
				#	values_list.remove(0)
				# themin = findmin(therange, min(values_list))
				# themax = findmax(therange, max(values_list))
				# rangelist = buildranges(themin, themax, therange) #[('990-1020', (990, 1020))]
				# for x in rangelist:
				#	v =	 FacetValue(name=x[0], facet=self, hierarchytype='range', hierarchyextra=x[1], 
				#						mask=self.mask)
				#	self.add_facetvalue(v)


		# Finally
		return [all_values, valid_values]	







	def _calcvaluesForORQueries(self, reversed_paths_list, facetModel):
		"""
			2012-04-25: this method haven't been updated with new MPTT stuff. TO bE REVISED
			
			This method can be very time-expensive as OR queries with lots of JOINs take a long time
		   We suggest to avoid OR queries if possible, and if needed create auxiliary tables...
		"""
		resulttypeName, facet, activeIDs, queryargs, LIMIT = self.resulttypeName, self.facet, self.activeIDs, self.queryargs, self.limit
		resulttypeModel = self.resulttypeModel
		dbfield = facet.originalAttribute
		if not queryargs or resulttypeModel._meta.proxy:	 # if have args (resulttypeModel._meta.proxy means than we can't use the default manager!)
			if resulttypeModel._meta.proxy:
				djfacetlog("resulttypeModel._meta.proxy == True!")
				activeIDs = list(set(activeIDs).intersection(set([x.id for x in resulttypeModel.objects.all()])))	
			args = []
			for path in reversed_paths_list:
				temp = {}
				if path:
					temp[path + "__id__in"] = activeIDs
				else:  # if path is '' or null
					temp["id__in"] = activeIDs
				args.append(Q(**temp))
			or_args = reduce(operator.or_,args)			

			# 1) get all possible valid facetValues, without counting
			
			#	2010-08-12 => added the Count, cause this way we're sure we have no duplicates! 
			djfacetlog("....starting query calculation......")		
			if facet.ordering:
				tot_allvalues = facetModel.objects.filter(or_args).values(dbfield).annotate(Count(dbfield)).count()
				valid_values = facetModel.objects.filter(or_args).values(dbfield).annotate(Count(dbfield)).order_by(facet.ordering)[:LIMIT]
			else:
				tot_allvalues = facetModel.objects.filter(or_args).values(dbfield).annotate(Count(dbfield)).count()
				valid_values = facetModel.objects.filter(or_args).values(dbfield).annotate(Count(dbfield))[:LIMIT]			
		else:  
			if facet.ordering:
				tot_allvalues = facetModel.objects.values(dbfield).annotate(Count(dbfield)).count()
				valid_values = facetModel.objects.values(dbfield).annotate(Count(dbfield)).order_by(facet.ordering)[:LIMIT]
			else:
				tot_allvalues = facetModel.objects.values(dbfield).annotate(Count(dbfield)).count()
				valid_values = facetModel.objects.values(dbfield).annotate(Count(dbfield))[:LIMIT]			


		if facet.hierarchyoptions:	# TO BE IMPLEMENTED 
			pass   # eg result: [{'count': 1, 'forename': u'Abraham'}, {'count': 1, 'forename': u'Aceard'},etc...]

		# 2) for each value, run the intersection routine to find out the count
		
		output = []
		counter = 0
		tot_limitvalues = len(valid_values)
		remaining_values = tot_allvalues - tot_limitvalues
		djfacetlog("____________ ==> got the possible facet values _____________ tot: %s (limit=%s)\nUsing MANUAL COUNT algorithm because we have an OR query....\n" % (str(tot_limitvalues), str(LIMIT)))
		for value in valid_values:
			counter += 1
			try:  #something this fails due to ascii encoding errors
				djfacetlog("===>> updating FV count for value: *%s* ==> [%d of %d]" % (str(value[dbfield]), counter,  tot_limitvalues))
			except:
				pass
			args = []
			# 2.1) construct the query as if we were querying the result (in the facetedManager)
			for behavior in self.getBehaviourTuple():
				temp = {}
				temp[behavior] = value[dbfield] 
				args.append(Q(**temp))
			or_args = reduce(operator.or_,args) 
			# 2.2) do the intersection of activeObjects with objects that have a certain value in facet
			#	   Count them, this is the number we're looking for
			if queryargs:	 # if have args
				number = resulttypeModel.objects.filter(id__in=activeIDs).filter(or_args).distinct().count()
			else:
				number = resulttypeModel.objects.filter(or_args).distinct().count()
			# djfacetlog('noise')	
			# djfacetlog(number)	
				
			# 3) find the facetValue object, and update the count
			
			if number:
				fv = facet.get_facetvalue_from_name(value[dbfield])
				if fv:
					fv_copy = copy.copy(fv)	 #make a copy, so we don't update the static FM object
					fv_copy.howmany = number
					fv_copy.tot_left = remaining_values
					fv_copy.tot_inbatch = tot_limitvalues
					fv_copy.tot_all = tot_allvalues
					output.append(fv_copy)
		if facet.exclude:  # this is just to flag it up: the real exclusion happens at FM loading time (see facet.py)
			djfacetlog("=====>> ****** excluding values found in facet.exclude: %s" % str(facet.exclude))
		return output












