from django.db.models.base import ModelBase
from django.db.models.query import QuerySet
from django.db.models import Avg, Max, Min, Count, Q
import operator

from fb_utils.utils import djfacetlog
from djfacet.constants import *


from djfacet.cache_manager import *
from djfacet.models import * 
from djfacet.facet import *
from djfacet.facetsgroup import *
from djfacet.facetvalue import *
from djfacet.queryhelper import *

from django.core.cache import cache








##################
#  
#  IMPORTANT AUXILIARY METHOD: GETS OR CREATES THE FACETED MANAGER OBJECT WHEN NEEDED
#
##################



def access_fmglobal(FORCE_CREATION=False):	# force_creation is used to avoid using the cached DB 
	""" 
	Method for loading the Faceted Manager instance and keeping it in memory.
		-> if not loaded already (at server start time) it's loaded from the DB (using pickle)
			-> if the DB cache is disabled, it loads it in memory using the global variable
				-> mind that this last option is not thread safe, so it shouldn't be used in the production environment!!
				-> if using the DB, first issue: 'python manage.py fb_store_facetmanager'
	 """
	FM_GLOBAL = cache.get('DJ_FM_GLOBAL')

	if FORCE_CREATION or ((not DJF_CACHE) and (not FM_GLOBAL)):		
		if not FORCE_CREATION:
			djfacetlog("\n\n***********\nInitializing FM_GLOBAL without the cached DB object\n[For faster performance you can pre-initialize the Faceted Manager instance and store it in the DB\nUse the management command 'djfacet_fmcache', and set DJF_CACHE = True in settings.py]\n***********\n", True)
		else:
			djfacetlog("\n\n***********\nInitializing FM_GLOBAL with <FORCE_CREATION=True>\n***********\n", True)
		loaded_facet_groups = []
		facets_for_template = []

		# load facet specs and init the Faceted Manager object
		# 1: create groups from SPECS.facet_groups	//	2: load facets into groups using SPECS.facetslist
		valid_groups = [x for x in reversed(sorted(DJF_SPECS.facet_groups, key=lambda (k): k['position'])) if x['default']]
		for n in range(len(valid_groups)):
			x = valid_groups[n]
			bkcolor = x.get('bkcolor', getHTMLColor(n))
			loaded_facet_groups.append(FacetsGroup(x['uniquename'], x['label'], x['position'], bkcolor=bkcolor)) 
		for g in loaded_facet_groups:
			g.buildfacets_fromspecs(DJF_SPECS.facetslist)

		RESULT_TYPES = DJF_SPECS.result_types 

		# initialize the faceted manager and add it to the django cache

		FM_GLOBAL = FacetedManager(loaded_facet_groups, RESULT_TYPES)
		cache.set('DJ_FM_GLOBAL', FM_GLOBAL, 600)  # 10 minutes
		

	if DJF_CACHE and not FM_GLOBAL and not FORCE_CREATION:
		djfacetlog("\n\n***********\nInitializing FM_GLOBAL: using database-cached version and LOCK mechanism to make it thread-safe\n***********\n", True)
		from django.db import connection
		cursor = connection.cursor()
		try:
			cursor.execute('LOCK TABLES %s WRITE' % 'djfacet_cachedfacetedmanager')
			x = CachedFacetedManager.objects.all()[0]
			FM_GLOBAL = x.manager
		except:
			raise Exception("\n***** DJFACET : could not init the Faceted Manager object from Database: have you created it? Use the 'djfacet_fmcache' management command to create it, or set DJF_CACHE to False")
		finally:
			cursor.execute('UNLOCK TABLES')
			cursor.close()
		cache.set('DJ_FM_GLOBAL', FM_GLOBAL, 600)  # 10 minutes

	# finally:	
	# if True:
	# 	clearExpiredSessions()

	return FM_GLOBAL






	##################
	#  
	#  FACETEDMANAGER CLASS : abstracts the common operations needed for handling queries and storage of facets
	#
	##################
	



class FacetedManager(object):
	""" 
	The manager contains and can access information about all the FacetsGroups and Facets. 
	
	The manager performs operations based on current queryargs and activeIDs: eg 'optimize_query', 'run_query', 'refresh_facetvalues'
	(queryargs = just a list of facetvalues)
	
		=+=
		facetsGroups: what groups it contains
		result_types: a list of dicts like this: 
					{	'label' : 'Ltb Records', 
						'uniquename' : 'ltbrecord', 
						'infospace' : Record	}
						+ added:
					{	'all_IDs' : [1, 3, 4, 5]
						'total_count' : 4 }
		=+=									
		
	"""

	def __init__(self, facetsGroups=None, result_types=None):
		# self.queryargs = []
		self.result_types = result_types
		self.ramcache = None  # the in Ram cache object
		if self.result_types:  #let's cache all the IDs for faster performance!!
			for r in self.result_types:
				r['all_IDs'] = None
				r['total_count'] = 0
		# self.activeIDs = None
		if facetsGroups:
			self.facetsGroups = []
			for i in facetsGroups:
				self.add_facetGroup(i)
		else:
			self.facetsGroups = []
		# initialize only the count at this time
		self.init_resulttypes_count()



	def add_facetGroup(self, facetG):
		self.facetsGroups.append(facetG)

	def get_facetGroup_from_name(self, uniquename):
		"""returns a facetGroup object from its name"""
		for x in self.facetsGroups:
			if x.uniquename == uniquename:
				return x
		return None

	def get_facet_from_name(self, uniquename):
		"""returns a facetGroup object from its name"""
		for x in self.get_all_facets():
			if x.uniquename == uniquename:
				return x
		return None


	def get_facetvalue_from_id(self, valueid):
		"""returns a facetGroup object from its name"""
		for group in self.facetsGroups:
			test = group.get_facetvalue_from_id(valueid)
			if test:
				return test
		return None


		
	def get_all_facets(self, group=None):
		"""
		eg: fm.get_all_facets(f.get_facetGroup_from_name('peoplegroup'))
		"""
		res = []
		if not group:
			for group in self.facetsGroups:
				for facet in group.facets:
					res.append(facet)
		else:
			for facet in group.facets:
				res.append(facet)
		return res
	

	def explain_queryargs(self, queryargs, result_type):
		response = {}
		if queryargs:
			for arg in queryargs:
				facet_obj = arg.facet
				facet_val = arg
				response[facet_val.name] = facet_obj.get_behaviour(result_type, True) 
		return response



	def all_results(self, resulttype_name): 
		"""Method to return all the objects in an information space. Usually, this is a django model, 
		   so we are just calling the objects.all() method on it. But the information space
		   could be represented by a QuerySet instance"""

		resulttype = self.get_resulttype_from_name(resulttype_name)
		infospace = resulttype['infospace']

		if isinstance(infospace, ModelBase):
			django_model = infospace
			return django_model.objects.all()
		elif isinstance(infospace, QuerySet):
			custom_queryset = infospace
			return custom_queryset
		else:
			return False


	def get_resulttype_from_name(self, name):
		"""get the result_type dictionary from the name """
		for i in self.result_types:
			if i['uniquename'] == name:
				return i
		return None


	def get_resulttype_allIDs(self, name):
		"""get the result_type allIds from the name """
		for i in self.result_types:
			if i['uniquename'] == name:
				return i['all_IDs']
		return None

	def get_resulttype_count(self, name):
		"""get the TOTAL NUMBER of result_type allIds from the name """
		for i in self.result_types:
			if i['uniquename'] == name:
				return i['total_count']
		return None



	def init_resulttypes_count(self):
		"""init the TOTAL NUMBER of result_type allIds from the name """
		for i in self.result_types:
			if DJF_CACHE:
				cachedResult = CachedFacetQuery.objects.filter(facet='None', resulttype=i['uniquename'])
				if cachedResult:
					i['total_count'] = cachedResult[0].tot_ids
					djfacetlog("INITIALIZED total count for -- %s -- from Database CACHE" % i['uniquename'])
				else:
					queryset = self.all_results(i['uniquename'])
					if queryset:
						i['total_count'] = queryset.count()
						djfacetlog("Tried to initialize from database Cache .. FAILED for -- %s --" % i['uniquename'])
						djfacetlog("INITIALIZED total count without Cache for -- %s --" % i['uniquename'])
			else:
				queryset = self.all_results(i['uniquename'])
				if queryset:
					i['total_count'] = queryset.count()
					djfacetlog("INITIALIZED total count for -- %s --" % i['uniquename'])



	def init_resulttypes_activeIDs(self, resulttype_name = None):
		""" This is not called at loading time, but only when necessary....
			- if a specific result type is passed, we calculate the list of all IDs and return it
			- if no arg is passed, we just calculate the TOT active IDs for all res types 
		"""
		if resulttype_name:
			res_type = self.get_resulttype_from_name(resulttype_name)
			queryset = self.all_results(resulttype_name)
			if queryset and not res_type['all_IDs']:
				res_type['all_IDs'] = [x.id for x in queryset]
				djfacetlog("INITIALIZED tot active IDs for -- %s --" % resulttype_name)
				return res_type['all_IDs']
		else:
			for res_type in self.result_types:
				queryset = self.all_results(res_type['uniquename'])
				if queryset and not res_type['all_IDs']:
					djfacetlog("INITIALIZED tot active IDs for -- %s --" % res_type['uniquename'])
					res_type['all_IDs'] = [x.id for x in queryset]


	# ======
	# QUERY section
	# ======
			

	def optimize_query(self, queryargs, resulttype_name):
		""" Changes the order of queryargs for better performance [2010-11-03]

			At the moment it works only if DB-CACHING is ON: it reorders the args depending on the number of 
			results they might produce (these are stored in CachedFacetValue table as 'count'). 
			The queryarg producing less results is applied first to the queryset filtering routine. 
			
			TODO: when there's no cache (=actively update db-FB) ... we should probably first launch the queries that have
			less joins (so to reduce the number of results), then the others..
		 """

		if DJF_CACHE:  # TODO FIX QUERYARGS
			djfacetlog("RUN_QUERY: optimizing queryargs order through cached values....")
			cacheDB = DbCache(self, queryargs, None)
			queryargs = cacheDB.updateQueryargsOrder_bycount(resulttype_name)
			cacheDB = None
		return queryargs




	def run_query(self, queryargs, resulttype_name, activeIDs, ordering = 'default', action = 'default'):
		"""		
		Method for running a query on the information space (which is dependent on the 
			resulttype value passed). 
						
		queryargs = a list of facetvalues 
		resulttype_name = string representing what result-types are selected (e.g., 'people')
		activeIDs = list of the objects-IDs in current result set
		action = the type of filtering action to be done (eg zomming in/out)
		
		TODO: 
		<explain algorithm>
				
		"""

		infospace = self.all_results(resulttype_name)  # returns the top-level queryset
		if not infospace: 
			raise Exception, "RUN_QUERY: Error: result type not found - could not continue"
	
		result = infospace
	
		if action == 'all':
			djfacetlog("RUN_QUERY: *all* action......")
			djfacetlog("ActiveIDs: %d [the entire result set!]" % self.get_resulttype_count(resulttype_name))
			djfacetlog("====now setting ActiveIDs to zero...." )
			activeIDs = []
	
		if action == 'add':
			# Adding 1 new filter: we try to speed up the query by re-using the previously stored active-IDs
			# NOTE: this approach will fail if we remove the activeIDs from the session object!
			djfacetlog("RUN_QUERY: *add* action... building queryset object using [%s] args.... " % len(queryargs))
			if len(queryargs) > 1:
				djfacetlog("RUN_QUERY: args>1 & action=add ==>	I'm using the *most recent queryarg* and the *cached activeIds* to speed up the query" )
				result = result.filter(id__in=activeIDs)

			result = self._inner_runquery(result, queryargs[-1], resulttype_name)  # even in case when 1 qarg only is present, [-1] gets the right one
			djfacetlog("====now updating ActiveIDs ...." )
			activeIDs = [x.id for x in result]
			djfacetlog("ActiveIDs: %d" % len(activeIDs))
				
				
		if action == 'remove' or action == 'reload':	
			djfacetlog("RUN_QUERY: *%s* action... building queryset object using [%s] args.... " % (action, len(queryargs)))

			if len(queryargs) > 1:
				queryargs = self.optimize_query(queryargs, resulttype_name)
				for i in range(len(queryargs)):
					if i == 0:
						djfacetlog("___calculating queryArg[%d]...." % (i + 1) )
						result = self._inner_runquery(result, queryargs[i], resulttype_name)

					else:
						djfacetlog("___calculating TEMP IDs for queryArg[%d]...." % (i + 1) )
						temp_IDs = [x.id for x in result]
						result = infospace.filter(id__in=temp_IDs)
						result = self._inner_runquery(result, queryargs[i], resulttype_name)
						
						if (i + 1) == (len(queryargs)):
							djfacetlog("====now updating ActiveIDs ...." )
							activeIDs = [x.id for x in result]
							djfacetlog("ActiveIDs: %d" % len(activeIDs))

			elif len(queryargs) == 1:
				result = self._inner_runquery(result, queryargs[0], resulttype_name)
				djfacetlog("====now updating ActiveIDs ...." )
				activeIDs = [x.id for x in result]
				djfacetlog("ActiveIDs: %d" % len(activeIDs))
			
			else:  # if we have no queryargs
				djfacetlog("ActiveIDs: %d [the entire result set!]" % self.get_resulttype_count(resulttype_name))
				djfacetlog("====now setting ActiveIDs to zero...." )
				activeIDs = []				
				
	
		# finally, let's do the ordering 
		# The 'annotate' syntax was LEFT for BACKWARD COMPATIBILITY, NOW ORDERING IS BETTER EXPRESSED AS A LIST OF STRINGS
		if type(ordering) == type('a string') or type(ordering) == type(u'a unicode string'):	
			if ordering == 'default':				
				return (activeIDs, result)			
			else:		
				if ordering.split('=')[0] == 'annotate':
					val = ordering.split('=')[1]
					result = result.annotate(Count(val)).order_by(val + '__count')
					return (activeIDs, result)
				elif ordering.split('=')[0] == '-annotate':
					val = ordering.split('=')[1]
					result = result.annotate(Count(val)).order_by('-' + val + '__count')
					return (activeIDs, result)
				elif ordering.find(",") > 0: 
					multiplevals = [x.strip() for x in ordering.split(',')]
					result = result.order_by(*multiplevals)
					return (activeIDs, result)
				else:
					result = result.order_by(ordering)
					
		else:  # ordering is a list of strings....
			result = result.order_by(*ordering)
			return (activeIDs, result)




	def _inner_runquery(self, queryset, queryarg, resulttype_name):
		"""	  
		queryset = a django queryset (e.g. the infospace, the result of a previous query)
		queryarg: a single facet value
		resulttype_name

		ALGORITHM: 
		
		The standard way to costruct dymanic queries with Django is by using **kwargs and exploding it in the query. 
		However this generates a problem when you want to add together two constraints on the same attribute, 
		for in such situation the query is interpreted differently.
			See also: http://docs.djangoproject.com/en/dev/topics/db/queries/#spanning-multi-valued-relationships 
		
		So the chain of 'filters' solution has been adopted, e.g.: 		

		Person.objects.filter(genderkey__fullname='Female', genderkey__fullname='Male')
		==> returns only the Males!!!

		Person.objects.filter(genderkey__fullname='Female').filter(genderkey__fullname='Male')
		==> this is what we want!!! (persons that are both male and female = None)
		
		
		In the case of MPTT filters (=hierarchical facets), if the relationships haven't been manually exploded 
		(i.e. if DJF_MPTT_INHERITANCE is True) we must look for matching results across the whole descendants in a tree.
		This is done by extracting a list of IDs of the descendants for a facetvalues, and passing those in the query.
		E.g. kwargs[linkAttr	 +	"id__in"] = descendants

		""" 

		args, kwargs, new_queryset = [], {}, queryset
		linkAttr = ""  # the behaviour specified in the specs = a string or tuple for complex ORs
		rangeAttr = ""	# the range specs
		facet, facetvalue = queryarg.facet, queryarg

		if not facet.get_behaviour(resulttype_name) == None:   # blank is valid behaviour!!!	 

			if facetvalue.customvalues: 
				# CASE 1: we are dealing with custom facets:
				# ******
					# e.g. {'hammondnumber' : 1, 'hammondnumb2__gt' : 0, 'hammondnumb2__lt' :10}
					# mind 1) with custom values, in the 'behavior' you must omit the last bit, ie the 'dbfield'
					# mind 2) that in queries with multiple joins there are two options to build the filters
					# 1) sequencing single .filter(...) arguments and 2) one single filter with all args inside
					# here we were forced to use the second one, as the 1st one would break with many joins (!)
					# it's an issue that requires further investigation.... 
					# http://docs.djangoproject.com/en/dev/topics/db/queries/#spanning-multi-valued-relationships
				linkAttr = facet.get_behaviour(resulttype_name)		#.behaviour[resulttype_name][0]
				if linkAttr:
					linkAttr = linkAttr + "__"
				for d in facetvalue.customvalues:
					# temp = {}
					kwargs[linkAttr + d] = facetvalue.customvalues[d]
					djfacetlog("==queryArg found... with CustomValues: [%s]" % (kwargs))
				new_queryset = new_queryset.filter(**kwargs).distinct()
				return new_queryset

			else:	
				# CASE 2: we are using Django-based facets (= models):
				# ******			
				valore = facetvalue.name
				linkAttr = facet.get_behaviour(resulttype_name)	  #.behaviour[resulttype_name][0]

				# SUBcase 1: if we have a behaviour encoded in a single 'string'
				# ----------
				if type(linkAttr) == type(""):	
					# ++++++++++++++++
					# 1.1 MPTT facets
					# ++++++++++++++++
					if facet.mptt and DJF_MPTT_INHERITANCE:
						
						mpttinstance = facet.originalModel.objects.get(pk=facetvalue.mpttoriginalID)
						
						descendants = [x.id for x in mpttinstance.get_descendants(True)] # includes this element too
						if facet.originalAttribute:
							# since we're completely replacing the original attribute of a query with the MPTT tree information, 
							# we need to remove that querypath element from the querypath defined in facetspecs. 
							# Eg: from <religions__name> to <religions__>
							linkAttr = linkAttr.rstrip(facet.originalAttribute)
						
						kwargs[linkAttr	 +	"id__in"] = descendants
						djfacetlog("==queryArg found... query with MPTT behaviour: [%s]" % (kwargs,))
						new_queryset = new_queryset.filter(**kwargs).distinct()

					else:	
						# ++++++++++++++++
						# 1.2 Normal facets
						# ++++++++++++++++				 
						if facetvalue.hierarchytype == 'alpha':
							rangeAttr = "__istartswith"
						if facetvalue.hierarchytype == 'range':
							rangeAttr = "__range"
							valore = facetvalue.hierarchyextra  # a tuple (100, 2000)
						# 	finally: 
						kwargs[linkAttr	 +	rangeAttr] = valore		# a dict
						djfacetlog("==queryArg found... with basic behaviour: [%s]" % (kwargs))
						new_queryset = new_queryset.filter(**kwargs).distinct()
						
					return new_queryset

				# SUBcase 2: if we have a behaviour encoded in a tuple=	 OR queries
				elif type(linkAttr) == type(("a tuple",)):						
					for el in linkAttr:
						temp = {}
						# added the range behaviour also here, but haven't tested yet!
						if facetvalue.hierarchytype == 'alpha':
							rangeAttr = "__istartswith"
						if facetvalue.hierarchytype == 'range':
							rangeAttr = "__range"
							valore = facetvalue.hierarchyextra 
						temp[el + rangeAttr] = valore
						djfacetlog("==queryArg found... with OR behaviour: [%s]" % (temp))
						args.append(Q(**temp))

					or_args = reduce(operator.or_,args) #make it a sequence of ORs
					new_queryset = new_queryset.filter(or_args, **kwargs).distinct()
					return new_queryset






	def refresh_facetvalues(self, queryargs, activeIDs, resulttype_name, facet, LIMIT=None, showonly_subs=False):
		"""
		************
		Method called to instantiate the QueryHelper and refresh the FacetValues count for the active query.
		
		<activeIDs>: precalculated list of object IDs, essential for running this method. 
					If not available (eg because the session has expired, or because a search page is loaded directly via a url) 
					needs to be recalculated via self.run_query
		<showonly_subs>: a flag indicating that we're only querying for the direct subs of a specific value
		*********
		"""
				
		# 1. test the DB cache	
		cache_test = None	
		if DJF_CACHE:
			djfacetlog("+++> DB-CACHE: .. trying to get values from DB for __%s__ ..." % facet.name)
			cacheDB = DbCache(self, queryargs, activeIDs)
			cache_test = cacheDB.getCachedFacetValues(resulttype_name, facet, LIMIT, showonly_subs)
			if cache_test:
				djfacetlog("	   -----> SUCCESS: Retrieved values.....")
				return cache_test
			else:
				cache_test = None
				djfacetlog("	   -----> FAILED: Could not retrieve any value from DB cache...")

		# 2. calculate the fv counts ==> cause the DBcache is switched off, or there's no cached data available
		if cache_test == None:			
			# if there are no facets selected, make sure we get the correct activeIDs number
			if not queryargs:
				saved_activeIDs = self.get_resulttype_allIDs(resulttype_name)
				if saved_activeIDs == None: 
					# .. if we still haven't cached all activeIDs, run 'init' 
					activeIDs = self.init_resulttypes_activeIDs(resulttype_name)										
				else:
					activeIDs = saved_activeIDs

				q = QueryHelper(resulttype_name, facet, activeIDs, queryargs, limit=LIMIT, showonly_subs=showonly_subs)
			
			else:
				if not activeIDs:
					# If the activeIDs got lost for some reason RUN THE QUERY AGAIN 
					# (the activeIDs are stored in the session for 5mins only.This makes it possible to open up a single_facet page from scratch too)
					djfacetlog("\n+++> REFRESH_FACETVALUES: ActiveIDs not available.... recalculating them........")
					activeIDs = self.run_query(queryargs, resulttype_name, activeIDs, action="reload")[0]
				q = QueryHelper(resulttype_name, facet, activeIDs, queryargs, limit=LIMIT, showonly_subs=showonly_subs)
				
			djfacetlog("\n+++> REFRESH_FACETVALUES:  calculating values using no cache for facet	 __%s__	 and LIMIT=%s" % (facet.name, str(LIMIT)))
			# calc the facetvalues using the QueryHelper obj...		
			valueslist = q.calculate_facetvalues()
			
			# CACHE ON THE FLY, IF IT'S A FULL QUERY ONLY
			if DJF_CACHE and not LIMIT and not showonly_subs:
				if not queryargs:
					result_type = self.get_resulttype_from_name(resulttype_name)		
					if cacheDB._cacheOneFacet(facet, result_type, values_to_cache=valueslist):
						djfacetlog("		  ...... on-the-fly DB-Cache operation successfull...!")
				else:
					pass # we're DB-caching on the fly only when there are no queryargs !!!!!!!! 
			
			# finally......
			return valueslist				
				





