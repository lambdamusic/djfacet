
##################
#  2011
#  NEW FILE VERSION FOR THREAD-SAFE, DB-CACHED, STATELESS FACETED MANAGER OBJECT 
#
##################

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect 
from django.template import RequestContext, Context, loader
from django.template.loader import select_template, get_template
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils.encoding import force_unicode

from djfacet.constants import *
from djfacet.cache_manager import *
from djfacet.load_all import *
from djfacet.fb_utils.utils import *
from djfacet.fb_utils.template import render_block_to_string

import datetime
import urllib









##################
#  
#  MAIN VIEWS 
#
##################


def home(request):
	"""
	Main dispatcher: checks if it is the first page (no filters and not item) of the FB, and redirects accordingly.
	
	The DJF_SPLASHPAGE constant defaults to True and indicates that the all_facets splash page is desired.
	
	The <search_page> view usually returns a (template, context) tuple; however if the query filters are invalid, it tries to remove the wrong ones, recompose the url and issue a redirect command. In this case a HttpResponseRedirect is returned, not a tuple, so an if statement handles that situation.
	 
	"""
	query_filtersUrl = request.GET.getlist('filter')
	item = request.GET.get('item', None)
	resulttype = validate_ResType(request.GET.get( 'resulttype', None ))
		
	if DJF_SPLASHPAGE and not query_filtersUrl and not item:
		# redirect to the all-facets page
		return redirect("allfacets/?resulttype=%s" % resulttype)	
	elif item:
		results = single_item(request, item) 
	else:
		# it's classic search page
		results = search_page(request)
	# finally..	
	if type(results) == type(('a tuple',)):
		template, context = results 
		return render_to_response(	template, 
									context, 
									context_instance=RequestContext(request))
	else:
		return results  # in this case it's a HttpResponseRedirect object




def single_item(request, item):
	"""
	"""
	FM_GLOBAL = access_fmglobal()
	page, resulttype, ordering, query_filtersUrl, query_filtersBuffer, activeIDs, item, totitems, showonly_subs, history = __extractGETparams(request)
	single_item_template, table_template =  None, None
	redirect_flag, query_filtersUrl_Clean = __validateQueryFilters(resulttype, query_filtersUrl, FM_GLOBAL)
	if redirect_flag:
		djfacetlog("FacetViews>> Redirecting; the url contained  invalid filter values!", True)
		newurl_stub = create_queryUrlStub(query_filtersUrl_Clean)
		newurl_stub = "%s?resulttype=%s%s" % (request.path, resulttype , newurl_stub)
		return redirect(newurl_stub)

	# HELPER URL STRINGA creation, from the active filters
	newurl_stub = create_queryUrlStub(query_filtersUrl)

	# CHECK THAT ITEM EXISTS
	try:
		item_obj = FM_GLOBAL.get_resulttype_from_name(resulttype)['infospace'].objects.get(pk=item)
	except:
		newurl_stub = "%s?resulttype=%s%s" % (request.path, resulttype , newurl_stub)
		return redirect(newurl_stub)
	
	
	if getattr(item_obj, "get_absolute_url", None):
		item_obj.fullrecord = True
	try:
		item_obj.next = activeIDs[activeIDs.index(item_obj.id)+1]
	except:
		pass
	try:
		i = activeIDs.index(item_obj.id)
		if i>0:
			item_obj.prev = activeIDs[i-1]
	except:
		pass
		
	# GET THE RIGHT TEMPLATE FOR RESULTS LIST	
	single_item_template = select_template([ "djfacet/%s/%s_item.html" % (resulttype, resulttype), 
										"djfacet/results/generic_item.html"])
	single_item_template = single_item_template.name

	if single_item_template == "djfacet/results/generic_item.html":
		# IF THE SINGLE_ITEM TEMPLATE IS THE DEFAULT ONE, JUST OUTPUT ALL FIELDS NAMES..
		this_model = FM_GLOBAL.get_resulttype_from_name(resulttype)['infospace']
		item_obj.fields = __getInstance_PreviewDict(this_model, item_obj)


	# UPDATE HISTORY
	history = update_history('single_item', history, item_obj, FM_GLOBAL.get_resulttype_from_name(resulttype), newurl_stub)
	request.session['djfacet_history']  = history				
		
	context = {	  
		'user_is_logged_in' : request.user.is_authenticated(),		

		'DJF_STATIC_PATH' : DJF_STATIC_PATH,
		'ajaxflag' : DJF_AJAX,
		'twocolumnsflag' : False,

		'result_types' : DJF_SPECS.result_types,	
		'result_typeObj' : FM_GLOBAL.get_resulttype_from_name(resulttype),	  
		'ordering' : ordering,

		'query_filtersBuffer' : query_filtersBuffer,
		'newurl_stub' : newurl_stub,

		'single_item' : item_obj,
		'single_item_template' : single_item_template,
		
		'recent_actions' : history

		}


	return ('djfacet/facetedbrowser.html', context)
			



def allfacets(request):
	"""
	View that shows a preview of all the facets in a single page; 

	The DJF_SPLASHPAGE_CACHE allows to use/create a cached version of the all_facets page. This may be useful
	when you have a lot of facets/values to display and want to reduce loading time. 
	"""
	if DJF_SPLASHPAGE_CACHE:
		resulttype = validate_ResType(request.GET.get( 'resulttype', None ))
		cached_page = get_cachedHTMLpage( "all_facets", extraargs=resulttype)
		if cached_page:
			return HttpResponse(cached_page)
		else:  # second parameter is CACHE_ONTHEFLY
			return HttpResponse(__allfacets_view(request, DJF_SPLASHPAGE_CACHE))  
	else:
		template, context = __allfacets_view(request)
	return render_to_response(	template, 
								context, 
								context_instance=RequestContext(request))



def search_page(request):
	"""
	Function that returns a tuple (template, context). 
	
	Normally it's used to calculate a query from one or more filters. 
	(if DJF_SPLASHPAGE_CACHE is set to False, it returns all values and all facets) 
	
	"""
	FM_GLOBAL = access_fmglobal()
	page, resulttype, ordering, query_filtersUrl, query_filtersBuffer, activeIDs, item, totitems, showonly_subs, history = __extractGETparams(request)
	table_template = None

	# CHECK THAT THE IDS PASSED IN FILTERS_URL ARE EXISTING AND VALID FOR THIS RESULT TYPE, otherwise redirect
	redirect_flag, query_filtersUrl_Clean = __validateQueryFilters(resulttype, query_filtersUrl, FM_GLOBAL)
	if redirect_flag:
		djfacetlog("FacetViews>> Redirecting; the url contained  invalid filter values!", True)
		newurl_stub = create_queryUrlStub(query_filtersUrl_Clean)
		newurl_stub = "%s?resulttype=%s%s" % (request.path, resulttype , newurl_stub)
		return redirect(newurl_stub)
	
	# ORDERINGS: if not provided it defaults to the standard one (as defined in the model)
	try:
		from djfacet.orderings import determine_ordering
		real_ordering = determine_ordering(resulttype, ordering)
	except:
		real_ordering = 'default'
	
	# =========	
	# UPDATE_RESULTS (note: new_queryargs has the new format=list of fvalues!)
	new_items, new_queryargs, new_activeIDs = __update_results(resulttype, real_ordering, query_filtersUrl, query_filtersBuffer, activeIDs)
	# =========
	
	
	# PAGINATION  
	 # ===>> rem that: 'items' is not a collection, so they are accessed through 'objects_list' method in the template
	paginator = Paginator(new_items, DJF_MAXRES_PAGE) # ie show 50 items per page
	try:
		items = paginator.page(page)
	except (EmptyPage, InvalidPage):  # If page request is out of range, deliver last page of results.
		items = paginator.page(paginator.num_pages)
	# add other useful paginator data to the object
	items.extrastuff = paginator_helper(page, paginator.num_pages)
	items.totcount = paginator.count

	# (RE)CREATE THE FACETS COLUMN:  new 2012-01-12 removed the <get_facetsForTemplate> routine
	facetgroups_and_facets = []
	if DJF_AJAX: 
		for group in FM_GLOBAL.facetsGroups: 
			# in this case we don't need to preload all facet contents, cause they'll be updated via ajax
			facetgroups_and_facets.append((group, [(facet, []) for facet in group.facets if facet.get_behaviour(resulttype)]))
	else:
		# set LIMIT to DJF_MAXRES_FACET/None to switch
		for group in FM_GLOBAL.facetsGroups:
			facetgroups_and_facets.append((group, 
				[(facet, FM_GLOBAL.refresh_facetvalues(queryargs=new_queryargs, activeIDs=new_activeIDs,
				 resulttype_name=resulttype, facet=facet, LIMIT=DJF_MAXRES_FACET)) for 
					facet in group.facets if facet.get_behaviour(resulttype)]))	
		
	# HELPER URL STRINGA creation, from the active filters
	newurl_stub = create_queryUrlStub(query_filtersUrl)
	
	# RESET THE SESSION INFO 
	request.session['query_filtersBuffer'] = new_queryargs	# a list of FValues..
	request.session['activeIDs'] = new_activeIDs	
	request.session['active_resulttype'] = resulttype	# a string (=uniquename) ... used by updateFacets	
	# print history
	history = update_history("search", history, new_queryargs, FM_GLOBAL.get_resulttype_from_name(resulttype), newurl_stub)
	request.session['djfacet_history']  = history	
	# print history
	# request.session.set_expiry(300) # 5 minutes ..	too much?


	# GET THE RIGHT TEMPLATE FOR RESULTS LIST
	table_template = select_template([ "djfacet/%s/%s_table.html" % (resulttype, resulttype), 
										"djfacet/results/generic_table.html"])
	table_template = table_template.name	
	
	context = {	  
		'user_is_logged_in' : request.user.is_authenticated(),
		'facetgroups_and_facets' :	 facetgroups_and_facets,	
		'items' : items,	
		'totitems' : items.totcount ,			

		'DJF_STATIC_PATH' : DJF_STATIC_PATH,
		'ajaxflag' : DJF_AJAX,
		'twocolumnsflag' : False,
		'djfacet_searchpage' : True,

		'result_types' : DJF_SPECS.result_types,	
		'result_typeObj' : FM_GLOBAL.get_resulttype_from_name(resulttype),	  
		'ordering' : ordering,

		'query_filtersBuffer' : new_queryargs,
		'newurl_stub' : newurl_stub,
		'table_template' : table_template,
		
		'recent_actions' : history

		}


	return ('djfacet/facetedbrowser.html', context)



	

def singlefacet(request, facet_name=None):
	"""
	2011-11-02: shows all the values available for a facet, and lets users select one  
	"""
	FM_GLOBAL = access_fmglobal()
	if facet_name and FM_GLOBAL.get_facet_from_name(facet_name):
		page, resulttype, ordering, query_filtersUrl, query_filtersBuffer, activeIDs, item, totitems, showonly_subs, history = __extractGETparams(request)
		
		redirect_flag, query_filtersUrl_Clean = __validateQueryFilters(resulttype, query_filtersUrl, FM_GLOBAL)
		if redirect_flag:
			djfacetlog("FacetViews>> Redirecting; the url contained  invalid filter values!", True)
			newurl_stub = create_queryUrlStub(query_filtersUrl_Clean)
			newurl_stub = "%s?resulttype=%s%s" % (request.path, resulttype , newurl_stub)
			return redirect(newurl_stub)
		
		newurl_stub = create_queryUrlStub(query_filtersUrl) 
		queryargs = [] 
		queryargs = [FM_GLOBAL.get_facetvalue_from_id(fvalue_id) for fvalue_id in query_filtersUrl]
		
		tree = None
		if showonly_subs:
			top_value = FM_GLOBAL.get_facetvalue_from_id(showonly_subs)
			if top_value:
				tree = FM_GLOBAL.get_facet_from_name(facet_name).recursive_tree_forfacetvalue(top_value)

		
		# print "\nARGs:\n",  showonly_subs, tree, "\n\n"

		djfacetlog("\n\n**** NewDJfacet Query ****\n\n.. action = SINGLE Facet\n... facet = %s \n.... resulttype = %s\n..... showOnlySubs = %s\n"% ( facet_name, str(resulttype), str(showonly_subs)), True)	
			
		context = {	  
			'user_is_logged_in' : request.user.is_authenticated(),
			'DJF_STATIC_PATH' : DJF_STATIC_PATH,
			'djfacet_singlefacet' : True,
			
			'result_types' : DJF_SPECS.result_types,	
			'result_typeObj' : FM_GLOBAL.get_resulttype_from_name(resulttype),	  
			'newurl_stub' : newurl_stub,
			'url_prefix' : "../../", # need to go up two levels!
			'facetvalues' : FM_GLOBAL.refresh_facetvalues(queryargs=queryargs, activeIDs=activeIDs,
			 				resulttype_name=resulttype, facet=FM_GLOBAL.get_facet_from_name(facet_name), showonly_subs=showonly_subs),
			'facet' : FM_GLOBAL.get_facet_from_name(facet_name), 
			'query_filtersBuffer' : queryargs,
			'totitems' : totitems,
			'tree' : tree
			}

		return render_to_response('djfacet/single_facet.html', 
									context,
									context_instance=RequestContext(request))
	else:
		raise Http404





##################
#  
#  HELPER METHODS 
#
##################




def update_history(action, past_history, new_step, resultType=None, queryStub=""):
	"""
	past_history: a list of tuples that vary depending on whether they represent objects-viewing or searches
	resultType: the resultType obj
	
	The history list is displayed in the control_history template. 
	"""
	MAXLEN = DJF_HISTORY_SIZE
	if not past_history:
		past_history = []
	new_history = past_history

	if action == "single_item":
		# in this case new_step is a Model instance: can't pass it as it is, cause it throws an error!
		newtuple = ("single_item", resultType, force_unicode(new_step), new_step.id, queryStub)
		
		if not (new_step.id in [x[3] for x in past_history]):
			new_history = [newtuple] + past_history

	if action == "search":
		# new_step is a list of queryargs (= facetvalues) for the current search
		newtuple = ("search", resultType, new_step, queryStub)
		
		if not (queryStub in [x[3] for x in past_history]):
			new_history = [newtuple] + past_history

	# djfacetlog("noise")
	if len(new_history) > MAXLEN:
		new_history.pop()
	return new_history






def __getInstance_PreviewDict(model, instance):
	"""
	Creates a dict with all of an instance's field names, plus values. Used in the single_item view, 
	for passing back to the template a simple representation of a mode instance.
	
	It could be done in one line like this:	
	fields = dict([(field, getattr(instance, field, None)) for field in this_model._meta.get_all_field_names() if getattr(instance, field, None)])	
	
	However that was failing when there are one-2-one relationships with emply values, so I changed it into a try/except routine	
	"""

	llist = [] 		
	for field in model._meta.get_all_field_names():
		try:
			test = getattr(instance, field, None)
		except: 
			test = False
		if test:
			llist.append((field, getattr(instance, field, None)))			
	return dict(llist)
	


def __extractGETparams(request):
	""" function that abstracts the process of getting all the GET parameters
	"""
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	try:
		item = int(request.GET.get('item', None))
	except:
		item = None
	try:
		totitems = int(request.GET.get( 'totitems', 0))
	except:
		totitems = 0
	resulttype = validate_ResType(request.GET.get( 'resulttype', None ))
	ordering = request.GET.get( 'ordering', 'default')	
	showonly_subs = 	request.GET.get( 'showsubs', None) #in single_facet, means that we're zooming into a specific filter-values
	query_filtersUrl = request.GET.getlist('filter')	# getlist gets all parameters with same name!!!!
	query_filtersBuffer = request.session.get('query_filtersBuffer', [])  # a list of fValues objects
	activeIDs = request.session.get('activeIDs', [])
	history = request.session.get('history', None)

	return [page, resulttype, ordering, query_filtersUrl, query_filtersBuffer, activeIDs, item, totitems, showonly_subs, history]


def __validateQueryFilters(resulttype, query_filtersUrl, FM_GLOBAL):
	"""
	Check That the Ids Passed in Filters_Url Are Existing and Valid for This Result Type
	Othersise return a flag, and a 'purified' version of the query filters, so that we can redirect the request to a valid URL
	-- This Way We Always Maintain a One-To-One Correspondance Between Url Filters and Args in Query
	
	MPTT values: this is a special case; if we find an MPTT value we check that there aren't any 'children' also selected as filters.
		If there are children, the father is removed cause the query is more specific. 
	"""
	redirect_flag, query_filtersUrl_Clean = False, [] 
	for fvalue_id in query_filtersUrl:
		try:
			facetvalue = FM_GLOBAL.get_facetvalue_from_id(fvalue_id)
			if facetvalue.facet.get_behaviour(resulttype) and not facetvalue.facet.mptt:
				query_filtersUrl_Clean.append(fvalue_id)
			elif facetvalue.facet.get_behaviour(resulttype):
				if facetvalue.facet.mptt:
					test_mpttfather = False
					all_vals = [FM_GLOBAL.get_facetvalue_from_id(x) for x in query_filtersUrl]
					for v in all_vals:
						if v.father and (v.father == facetvalue.id):
							test_mpttfather = True
					if 	test_mpttfather:
						redirect_flag = True	
						djfacetlog("FacetViews>> The requested facetvalue [%s] already has an MPTT children selected, thus it will be removed (resulttype [%s])"	% (fvalue_id, resulttype), True)
					
					else:
						query_filtersUrl_Clean.append(fvalue_id)	
																				
			else:
				redirect_flag = True
				djfacetlog("FacetViews>> The requested facetvalue [%s] doesn't have a behaviour for resulttype [%s]"	% (fvalue_id, resulttype), True)
		except Exception, e:
			redirect_flag = True
			djfacetlog("FacetViews>> Can't identify facetvalue from ID! Error: %s" % (e), True)
			continue 
	return (redirect_flag, query_filtersUrl_Clean)






def __allfacets_view(request, CACHE_ONTHEFLY=False):
	"""
	If we get here, it means that the Cache for the splash page hasn't been found

	If the 'CACHE_ONTHEFLY' variable is set to true, we store the cached-page after it's been calculated

	"""
	FM_GLOBAL = access_fmglobal()
	resulttype = validate_ResType(request.GET.get( 'resulttype', None ))	 

	# CREATE THE FACETS COLUMNS: 
	djfacetlog("\n\n**** NewDJfacet Query ****\n\n.. action = ALL Facets\n... resulttype = %s \n.... DJF_MAXRES_ALLFACETS = %s	  \n"% ( str(resulttype),  str(DJF_MAXRES_ALLFACETS)), True)	
	facetgroups_and_facets = []
	for group in FM_GLOBAL.facetsGroups:
		facetgroups_and_facets.append((group, [(facet, FM_GLOBAL.refresh_facetvalues(queryargs=[], activeIDs=[], resulttype_name=resulttype, facet=facet, LIMIT=DJF_MAXRES_ALLFACETS)) for facet in group.facets if facet.get_behaviour(resulttype)]))				

	# RESET THE SESSION INFO 
	request.session['active_resulttype'] = resulttype	# a string (=uniquename) ... used by updateFacets
	request.session['query_filtersBuffer'] = [] # a list of FValues..
	request.session['activeIDs'] = []
	# request.session.set_expiry(300) # 5 minutes ..	too much?

	context = {	  
		'DJF_STATIC_PATH' : DJF_STATIC_PATH,
		'user_is_logged_in' : request.user.is_authenticated(),
		'facetgroups_and_facets' :	 facetgroups_and_facets,			

		'ajaxflag' : False,	 # trick so that in this template the contents of facets are shown
		'twocolumnsflag' : True,
		'djfacet_splashpage' : True,

		'result_types' : DJF_SPECS.result_types,	
		'result_typeObj' : FM_GLOBAL.get_resulttype_from_name(resulttype),	  
		'newurl_stub' : "", # empty cause there are no filter here
		'url_prefix' : "../", # need to go up one level!
		}

	if CACHE_ONTHEFLY:		
		# render the template
		template = get_template('djfacet/all_facets.html')
		text = template.render(RequestContext(request, context))
		# cache it
		cacheHTMLpage(text, "all_facets", extraargs=resulttype)
		return text
	else:
		# rendering done somewhere else		
		return ('djfacet/all_facets.html', context)






def __update_results(resulttype, ordering, query_filtersUrl, query_filtersBuffer, activeIDs):
	""" 
	Method that runs a query via the faceted browser. 
	
	The new approach is that each query contains in the GET (query_filtersUrl) all the 
	necessary information for constructing queryargs. 
	The Buffer is used only to determine the 'action', when possible, and adopt alternative heuristics for faster performance

	RESULTTYPE: string representing what result-types are selected (e.g., 'factoids')
	ORDERING: string used to pass ordering directives (starts with '-' for descending order)

	"""

	FM_GLOBAL = access_fmglobal()
	items = None
		
	# remember that query_filtersBuffer is a list of FV objects, so the ID is a number, not a string!
	query_filtersBufferIDs = [force_unicode(x.id) for x in query_filtersBuffer if x]
				
	filters_difference = list_difference(query_filtersUrl, query_filtersBufferIDs)			

	if len(query_filtersUrl) == 0:
		action = "all"
	elif len(filters_difference) == 1:		
		if (len(query_filtersUrl) - len(query_filtersBufferIDs)) == 1:
			action="add"
			#make sure the latest element is last! (this is needed by the FM run_query algorithm)
			query_filtersUrl.remove(filters_difference[0])	
			query_filtersUrl.append(filters_difference[0])
		if (len(query_filtersBufferIDs) - len(query_filtersUrl)) == 1:
			action="remove" 
	else:
		# in all the other cases..we can't establish a continuity with the previous query (difference = 2 or more..) ... thus just apply the filters sequentially
		action = "reload"  
	
	# No need to check for valid Ids here: it's already been done in the 'Home' function
	#  TIP: we must set it to null first, in order to avoid caching!!!! 
	queryargs = [] 
	queryargs = [FM_GLOBAL.get_facetvalue_from_id(fvalue_id) for fvalue_id in query_filtersUrl]
	
	djfacetlog("\n\n**** NewDJfacet Query ****\n\n.. action = %s\n... query_filtersUrl = %s \n.... query_filtersBuffer_IDs = %s	  \n..... **filters_difference** = %s\n...... queryargs = %s\n"% (action, str(query_filtersUrl),  str(query_filtersBufferIDs), str(filters_difference), str([q.id for q in queryargs])), True)	
	djfacetlog("\n....ordering is %s\n" % str(ordering))
	
	# RUN THE QUERY
	result = FM_GLOBAL.run_query(queryargs, resulttype, activeIDs, ordering, action)
	new_activeIDs = result[0]
	items_list = result[1]
	
	djfacetlog("+++++++++++ FACETVIEW: new_activeIDs: [%d] ... now starting Pagination ....." % len(new_activeIDs))

	return [items_list, queryargs, new_activeIDs]









##################
#  
#  AJAX VIEWS 
#
##################






def update_facet(request):
	""" 
	Used in AJAX views to update the contents of a single facet
	"""
	
	FM_GLOBAL = access_fmglobal()
	page, resulttype, ordering, query_filtersUrl, query_filtersBuffer, activeIDs, item, totitems, showonly_subs, history = __extractGETparams(request)
	
	facet_name = request.GET.get('activefacet', None)
	facet = FM_GLOBAL.get_facet_from_name(facet_name)
	
	active_filters = request.GET.getlist('active_filters')	# values hard-coded in the html page!
	# print "\n\n++active_filters=	 " + str(active_filters)
	
	if not (facet and resulttype):
		return HttpResponse("An error occured: please reload the page. (resulttype=[%s] facet=[%s])" % (str(resulttype), str(facet_name)))

	
	# CHECK THAT THE IDS PASSED IN FILTERS_URL ARE EXISTING AND VALID FOR THIS RESULT TYPE, otherwise redirect
	redirect_flag, query_filtersUrl_Clean = __validateQueryFilters(resulttype, query_filtersUrl, FM_GLOBAL)
	if redirect_flag:
		djfacetlog("FacetViews>> Redirecting; the url contained  invalid filter values!", True)
		newurl_stub = create_queryUrlStub(query_filtersUrl_Clean)
		newurl_stub = "%s?resulttype=%s%s" % (request.path, resulttype , newurl_stub)
		return redirect(newurl_stub)
		
	# CHECK IF WE CAN USE THE SESSION DATA: if not, the back button has been utilized!
	if not len(query_filtersUrl) == len(query_filtersBuffer):
		activeIDs = []
		queryargs = [FM_GLOBAL.get_facetvalue_from_id(fvalue_id) for fvalue_id in query_filtersUrl]
		# RESET THE SESSION INFO 		
		request.session['query_filtersBuffer'] = queryargs	# a list of FValues..
		request.session['activeIDs'] = activeIDs 
	else:
		queryargs = query_filtersBuffer		
	# 
	# try: 
	# 	totitems = int(totitems)
	# except:
	# 	totitems = 0
	

	# TRY THIS TO DEBUG: WHEN YOU USE THE BACK BUTTON, IN CHROME, THE ACTIVEIDS ARE SET BACK TO 0!
	# WHILE IN SAFARI THIS NEVER HAPPENS...
	# print "\nqueryargs=%s\nactiveIDs=%s\nresulttype=%s\nfacet=%s" % (str(queryargs), str(len(activeIDs)), str(resulttype), str(facet))	
	newvalues = FM_GLOBAL.refresh_facetvalues(queryargs, activeIDs, resulttype, facet, LIMIT=DJF_MAXRES_FACET)
	# print "\n\n ____	" + str(newvalues)
	
	# HELPER URL STRINGA creation, from the active filters
	query_filtersBufferIDs = [force_unicode(x.id) for x in queryargs]
	newurl_stub = create_queryUrlStub(query_filtersBufferIDs)

	innerfacet_template = 'djfacet/components/snippet_facet.html'			

	context = Context({ 'facetvalues' : newvalues , 
						'facetgroup':	facet.group,
						'facet' :	facet,
						'newurl_stub' : newurl_stub,
						'result_typeObj' : FM_GLOBAL.get_resulttype_from_name(resulttype),	
						'totitems' : totitems or len(activeIDs),  #when using dbcache, totitems may fails
						'ordering' : ordering , 
						'DJF_STATIC_PATH' : DJF_STATIC_PATH,
						})
						
	return_str = render_block_to_string(innerfacet_template, 
											'inner_facet_values', 
											context)											
																						

	return HttpResponse(return_str)

















