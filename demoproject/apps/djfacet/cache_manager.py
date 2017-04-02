from django.db.models.base import ModelBase
from django.db.models.query import QuerySet
from django.db.models import Avg, Max, Min, Count, Q
from django.core.cache import cache
from  django.utils.encoding import force_unicode

import operator, copy


# from djfacet.load_all import *  ==> THIS WILL CAUSE A LOADING CONFLICT! 
from djfacet.constants import *
from djfacet.models import * 
from djfacet.facetsgroup import * 
from djfacet.queryhelper import *

from fb_utils.utils import *





##################
#  
#  DbCache : abstracts the common operations needed for handling queries and storage of DB-cached facet-values
#
##################



class DbCache(object):
	""" The manager contains information about .... 
		=+=
		For now, it is normally instantiated without queryargs, eg:
		cacheDB = DbCache(FM_INSTANCE)
		
		=+=
	
	"""
	
	def __init__(self, fManager, queryargs=None, activeIDs=None):
		self.fm = fManager
		self.queryargs = queryargs
		self.activeIDs = activeIDs
		if fManager:  #new 2011-10-05
			self.result_types = fManager.result_types



	##################
	#	CACHING methods
	##################


	def cacheResultTypes(self):
		""" caches the tot number of results """
		for res in self.result_types:	
			# NOTE: if a CachedFacetQuery obj has 'None' in facet name, then it's a tot res type 
			# ..maybe later we decide cache also the IDS with this function.. would that be an improvement?
			# THE tot counts have already been added when the FM has been instantiated
			# old ===>	   tot = res['total_count'] 
			
			# 2011-01-30: we force recounting the res-set 
			queryset_count = self.fm.all_results(res['uniquename']).count()
			try:
				obj = CachedFacetQuery.objects.get(facet='None', resulttype=res['uniquename'])
				djfacetlog("..updating TOT number of results in DBcache, for type %s" % res['uniquename'])
			except:
				obj = CachedFacetQuery(facet='None', resulttype=res['uniquename'])
				djfacetlog("..creating TOT number of results in DBcache, for type %s" % res['uniquename'])
			obj.tot_ids=queryset_count
			obj.save()



	def _cacheOneFacet(self, facet, resulttype,  ENFORCE = False, values_to_cache = None):
		"""
		FACET:	the facet within which we need to find the facet-values to cache
		RESULTTYPE: the result the facet-values to cache (and facet) are related to
		ENFORCE: even if already cached, it forces an update on the count of that object
		VALUES_TO_CACHE:  if we already pass the values to be cached, these are just saved..
		"""
	
		cached_fquery_old, cached_fquery_new = None, None
		queryargs = self.queryargs	

		# calculate queryargs transformation, get the CachedQueryArgs instance and pass it
		if queryargs: 
			exploded_queryargs = self.explodeQueryargs(queryargs)
			djfacetlog("cacheDB>> QUERYARGS found and transformed: **%s**"	% str(temp))
		else:
			exploded_queryargs = None

		# get the CachedFacetQuery instance
		try:
			cached_fquery_old = CachedFacetQuery.objects.get(facet=facet.uniquename, resulttype=resulttype['uniquename'], queryargs=exploded_queryargs)
		except:
			cached_fquery_new = CachedFacetQuery(facet=facet.uniquename, resulttype=resulttype['uniquename'], queryargs=exploded_queryargs)
		
		# ___________
		# DELETE previously cached stuff, if necessary
		# ___________
		if cached_fquery_old and ENFORCE:
			djfacetlog("cacheDB>>\n------\nENFORCE = true ===> emptying previously saved values......\n------")
			self._emptyCacheForFacetQuery(facet, resulttype, exploded_queryargs)
			# delete the previous contents first
		else:
			djfacetlog("cacheDB>> ENFORCE parameter not found (it's a new object or ENFORCE is set to false) => not deleting previously saved values")


		# ___________
		# CASE 1: we're passing some facet values with counts (eg when caching in real time while using the site). No need to calculate, just save in DB-cache tables
		# ___________
		if values_to_cache or values_to_cache == []:  # also if it's an empty list	 
			djfacetlog("cacheDB>>\n****\nCACHING ON THE FLY == Facet= *%s*	 Result= *%s*	Queryargs= *%s*\n****"	% (facet.uniquename, resulttype['uniquename'], str(exploded_queryargs)))		
			cached_fquery = cached_fquery_new or cached_fquery_old	
			cached_fquery.tot_ids = len(self.activeIDs)
			cached_fquery.save()
			self._inner_cache(cached_fquery, values_to_cache, facet, resulttype)
			return True

		# ___________
		# CASE 2: caching programmatically from console 
		# in this case we found a new cached_fquery to cache, or an old one with either ENFORCE_UPDATE or DELETE set to True.. 
		# ___________
		if cached_fquery_new or (cached_fquery_old and ENFORCE):
			# update the activeIDs as needed, instantiate the QueryHelper obj and save the instance
			djfacetlog("cacheDB>>\n****\nCACHING	 == Facet= *%s*	 Result= *%s*	Queryargs= *%s*\n****"	% (facet.uniquename, resulttype['uniquename'], str(exploded_queryargs)))		
			cached_fquery = cached_fquery_new or cached_fquery_old	

			# ___________ for the moment we're handling only queries with NO queryargs (= top level)
			
			djfacetlog("cacheDB>> Applying algorithm for top-level items (no QUERYARGS)")
			cached_fquery.tot_ids = self.fm.get_resulttype_count(resulttype['uniquename'])
			queryHelper= QueryHelper(resulttype['uniquename'], facet, resulttype['all_IDs'])
			cached_fquery.save()

			values_to_cache = queryHelper.calculate_facetvalues()
			self._inner_cache(cached_fquery, values_to_cache, facet, resulttype)
			return True
			
					
		# ___________		
		# CASE 3: final case.. nothing to cache, cause the object is already there
		# ___________
		else:
			djfacetlog("cacheDB>> Facet= *%s*	 Result= *%s* ........... Object already Cached!"	% (facet.uniquename,	resulttype['uniquename']))
			return False




	def _inner_cache(self, cached_fquery, values_to_cache, facet, resulttype):
		"""
		Does the caching of a list of facetvalues in the context of a specific cached_fquery
		Each facetvalue contains specific information eg updated counts or mptt-related stuff..
		"""
		counter = 0 
		counterTot = len(values_to_cache)
		for fv in values_to_cache:
			counter += 1
			try:
				djfacetlog("cacheDB>> Facet= *%s*	 Result= *%s*  Caching value %d of %d -- name[%s] count[%s]" % (facet.uniquename, resulttype['uniquename'], counter, counterTot, str(fv.name), str(fv.howmany)))
			except:
				djfacetlog("cacheDB>> Facet= *%s*	 Result= *%s*  Caching value %d of %d ... name couldn't be printed" % (facet.uniquename, resulttype['uniquename'], counter, counterTot))
			try:
				cacheValue = CachedFacetValue.get(facetvalue=fv.name)	# add facet=....
			except:
				cacheValue = CachedFacetValue(facetvalue=fv.name)	# add facet=....
			cacheValue.count=fv.howmany
			if facet.mptt:
				# 2012-05-23: extra data for mptt subs preview
				# cacheValue.subspreview is just a list of facetvalues
				subs_serialization = "**$**".join([x.id for x in fv.subspreview]) 
				cacheValue.mpttsubs = subs_serialization
			cacheValue.save()
			cached_fquery.facetvalues.add(cacheValue)


	def explodeQueryargs(self, queryargs):
		"""
		Creates a deterministic representation of queryArgs, so that they can be stored in the DB as field of  
		the CachedFacetQuery object
		==> returns: '123_12345_562719192'
		QueryArgs: list of facetvalues 

		This is useful for caching second-level queries.

		"""

		queryargs_Ids = [x.id for x in queryargs]
		return "_".join([force_unicode(x) for x in sorted(queryargs_Ids)])  # we sort them always by number




	##################
	#	GET methods
	##################

	def isIntegerField(self, model, field):
		"""Helper method for detecting facets that store value names as integers """
		x = model._meta.get_field(field)
		from django.db import connection 
		if 'integer' in x.db_type(connection=connection): 
			djfacetlog("..... integer field facetvalue exception detected...")
			return True
		else:
			return False


	def getCachedFacetValues(self, resulttype_name, facet, limit=1000000000000, showonly_subs=False):
		# if existing in DB-cache
		# return a list of facetValues, with counts
		# otherwise return None

		facet_uniquename = facet.uniquename
		if self.queryargs:
			queryargs = self.explodeQueryargs(self.queryargs)
		else:
			queryargs = None  # because it's an empty list otherwise...

		c = CachedFacetQuery.objects.filter(facet=facet_uniquename, resulttype=resulttype_name, queryargs=queryargs)
		if c:
			output = []
			flag = self.isIntegerField(facet.originalModel, facet.originalAttribute)
			c = c[0]  # there must be only one value, a CachedFacetQuery instance
			
			tot_allvalues = c.facetvalues.all().count()
			tot_limitvalues = limit or 0
			remaining_values = tot_allvalues - tot_limitvalues
			
			# get the right values from DB
			for val_obj in c.facetvalues.all()[:limit]:
				# sometimes a facet name is a number, not a string
				# but the caching table stores everything as strings, so we need an extra check here:
				if flag:
					fv = facet.get_facetvalue_from_name(int(val_obj.facetvalue))
				else:
					fv = facet.get_facetvalue_from_name(val_obj.facetvalue)						
				if fv and facet.mptt:
					if showonly_subs:
						# djfacetlog("noise")
						test_fv = facet.get_facetvalue_from_id(showonly_subs)
						if test_fv.id == fv.father:
							continue
						else:
							break							
					fv_copy = copy.copy(fv)	 #make a copy, so we NEVER update the static FM object (and it's thread-safe!)
					fv_copy.howmany = val_obj.count
					fv_copy.subspreview = [facet.get_facetvalue_from_id(x) for x in val_obj.mpttsubs.split("**$**") if val_obj.mpttsubs]
					fv_copy.tot_left = remaining_values
					fv_copy.tot_inbatch = tot_limitvalues
					fv_copy.tot_all = tot_allvalues
					output.append(fv_copy)

				elif fv:
					fv_copy = copy.copy(fv)	 #make a copy, so we NEVER update the static FM object (and it's thread-safe!)
					fv_copy.howmany = val_obj.count
					fv_copy.tot_left = remaining_values
					fv_copy.tot_inbatch = tot_limitvalues
					fv_copy.tot_all = tot_allvalues
					output.append(fv_copy)
								
			return output
		else:
			return None





	def getCachedFacetValue_fromValue(self, facet, resulttype_name, avalue):
		""" Same as above...... but just gets a single value from the DB cache

		>>> c = CachedFacetQuery.objects.filter(facet='gender', resulttype='source', queryargs=None)
		>>> c
		[<CachedFacetQuery: CachedFacetQuery object>]
		>>> CachedFacetValue.objects.filter(cachedfacetquery=c, facetvalue="M")
		[<CachedFacetValue: CachedFacetValue object>]
		>>> CachedFacetValue.objects.filter(cachedfacetquery=c, facetvalue="M").values('count')
		[{'count': 5998L}]

		"""
		the_FacetValueObj = None
		c = CachedFacetQuery.objects.filter(facet=facet.uniquename, resulttype=resulttype_name, queryargs=None)
		if c:  # eg: [<CachedFacetQuery: CachedFacetQuery object>]
			the_queryObj = c[0]
			flag = self.isIntegerField(facet.originalModel, facet.originalAttribute)
			if flag:  # is this the correct inverse of the one above?
				avalue = str(avalue)
			res = CachedFacetValue.objects.filter(cachedfacetquery=the_queryObj, facetvalue=avalue)
			if res:	 # eg: [<CachedFacetValue: CachedFacetValue object>]
				the_FacetValueObj = res[0]

		return	the_FacetValueObj	



	def getCachedFacetValueCount_fromValue(self, facet, resulttype_name, avalue):
		""" Same as above...... but just gets a single value-count from the DB cache

		"""
		val = self.getCachedFacetValue_fromValue(facet, resulttype_name, avalue)
		if val:
			return val.count
		return None



	def updateQueryargsOrder_bycount(self, resulttype_name):
		"""
		This is the main method that gets called when optimizing the order of queryargs: it checks the cache
		for the stored results number, and attaches it to the queryarg list.
		The queryargs list is returned reordered in increasing order (the vlue with less results first)

		QueryArgs: list of [active_facetsGroup, active_facet, facetvalue]  ==> the objects..
						==> get names using: active_facet.uniquename, facetvalue.name
		""" 
		temp = []
		for fvalue in self.queryargs:
			active_facet = fvalue.facet
			facetvalue = fvalue
			count = self.getCachedFacetValueCount_fromValue(active_facet, resulttype_name, fvalue.name)
			temp.append((fvalue, count))

		sorted_args = sorted(temp, key=lambda(x): x[1])
		djfacetlog("...CacheDB: optimization succesfull!") 
		return [x[0] for x in sorted_args]	# don't return the count!






	##################
	#	DELETE methods
	##################


	def _emptyUnusedElements(self):
		tot = 0
		for x in CachedFacetValue.objects.all():
			if not x.cachedfacetquery_set.all():
				djfacetlog("CachedFacetValue[id=%d] deleted..." % x.id)
				x.delete()
				tot += 1
		return tot


	def _emptyCacheForFacetQuery(self, facet, resulttype, queryargs=None):
		"""	 QueryArgs:	 a) list of [facetvalue1, facetvalue2 etc. ] 
						 b) keyword,  "only_with_queryargs" or "all"
						 c) a string of exploded queryargs "123_446_789"
		"""		
		if queryargs == "only_with_queryargs":	# special case
			try:
				obj_list = CachedFacetQuery.objects.filter(Q(facet=facet.uniquename), Q(resulttype=resulttype['uniquename']), ~Q(queryargs=None))
				# obj_list = CachedFacetQuery.objects.exclude(facet=facet.uniquename, resulttype=resulttype['uniquename'], queryargs=None)
			except:
				return "error with queryargs - ALL query"
			for obj in obj_list:
				for v in obj.facetvalues.all():
					v.delete()
				# if obj.queryargs:
				#	obj.queryargs.delete()
				djfacetlog("\n!!!!!!!!!... removing all cached objects .........\n facet[%s] resType[%s] queryargs=[NOT NULL]" % (facet.uniquename, resulttype['uniquename'],))			
				obj.delete()
			return True 

		elif queryargs == "all":	# special case
			try:
				obj_list = CachedFacetQuery.objects.filter(Q(facet=facet.uniquename), Q(resulttype=resulttype['uniquename']))
			except:
				return "error - couldn't get CachedFacetQuery obj list"
			for obj in obj_list:
				for v in obj.facetvalues.all():
					v.delete()
				# if obj.queryargs:
				#	obj.queryargs.delete()
				djfacetlog("\n!!!!!!!!!... removing all cached objects .........\n facet[%s] resType[%s] queryargs=[any]" % (facet.uniquename, resulttype['uniquename'],))			
				obj.delete()
			return True

		# case in which we have a list of queryargs to be transformed	
		elif type(queryargs) == type(["a list"]):  
			queryargs = self.explodeQueryargs(queryargs)


		elif type(queryargs) == type("a string") or type(queryargs) == type(u"a unicode string"):	 
			pass


		# finally: 
		try:
			cached_fquery_old = CachedFacetQuery.objects.get(facet=facet.uniquename, resulttype=resulttype['uniquename'], queryargs=queryargs)
		except:
			return "there is not such facet to delete in the cached DB table"
		djfacetlog("\n!!!!!!!!!!!!!!... removing all cached objects .........\n facet[%s] resType[%s] queryargs=[%s]" % (facet.uniquename, resulttype['uniquename'], str(queryargs)))
		for v in cached_fquery_old.facetvalues.all():
			v.delete()

		cached_fquery_old.delete()
		return True











##################
#  
# EXTRA UTILS FOR CACHING HTML PAGES IN THE DB 
#
##################


def cacheHTMLpage(text, pagename, extraargs="", ENFORCE=False):
	""" Caches the contents of a page (eg splash page) in the DB

	"""
	c = CachedHtmlPage.objects.filter(page=pagename, args=extraargs)
	if c and ENFORCE:
		c[0].contents = text
		c[0].save()
		djfacetlog("CACHEHTMLPAGE: The page [%s, %s] has been re-cached." % (pagename, extraargs))
	elif c and not ENFORCE:
		djfacetlog("CACHEHTMLPAGE: The page [%s, %s] is already cached. Use ENFORCE to recache it." % (pagename, extraargs))
	else:
		c = CachedHtmlPage(page=pagename, args=extraargs, contents=text )
		c.save()
		djfacetlog("CACHEHTMLPAGE: The page [%s, %s] has been cached for the first time." % (pagename, extraargs), True)


def get_cachedHTMLpage(pagename, extraargs=""):
	""" REtrieves the cached contents of a page (eg splash page) from the DB

	"""
	c = CachedHtmlPage.objects.filter(page=pagename, args=extraargs)
	if c:
		djfacetlog("GET_CACHEDHTMLPAGE: The page [%s, %s] has been retrieved from DB" % (pagename, extraargs), True)
		return c[0].contents
	else:
		djfacetlog("GET_CACHEDHTMLPAGE: The page [%s, %s] wasn't found in the cache." % (pagename, extraargs))
		return None


def delete_cachedHTMLpage(pagename, extraargs=""):
	""" Deletes the cached contents of a page (eg splash page) from the DB

	"""
	c = CachedHtmlPage.objects.filter(page=pagename, args=extraargs)
	if c:
		c.delete()
		djfacetlog("""DELETE_CACHEDHTMLPAGE: The page [%s, %s] has been deleted from DB\nIt will be automatically 
		re-cached the next time you set DJF_SPLASHPAGE_CACHE = True""" % (pagename, extraargs), True)
	else:
		djfacetlog("DELETE_CACHEDHTMLPAGE: the page [%s, %s] was not found in the cache" % (pagename, extraargs), True)
		return None











