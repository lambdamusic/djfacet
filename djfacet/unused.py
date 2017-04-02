

def OLD_splash_page(request):

	FM_GLOBAL = access_fmglobal()
	RESULT_TYPES = DJF_SPECS.result_types 
	DEFAULT_RESULTTYPE = get_defaultResType()

	# -------
	resulttype = request.GET.get( 'resulttype', None )	 # what result-types are selected (e.g., 'factoids')
	ordering = request.GET.get( 'ordering', 'default')	
	query_filtersUrl = [] 
	query_filtersBuffer = request.session.get('query_filtersBuffer', [])  # a list of fValues objects
	activeIDs = request.session.get('activeIDs', [])
	item = None	
	# -------

	if not resulttype or resulttype not in [x['uniquename'] for x in RESULT_TYPES]:
		resulttype = DEFAULT_RESULTTYPE['uniquename']

	# CREATE THE FACETS COLUMNS: 
	facetgroups_and_facets = get_facetsForTemplate([], activeIDs, resulttype)

	# HELPER URL STRINGA creation, from the active filters
	newurl_stub = create_queryUrlStub(query_filtersUrl)

	# RESET THE SESSION INFO 
	request.session['active_resulttype'] = resulttype	# a string (=uniquename) ... used by updateFacets
	request.session['query_filtersBuffer'] = []	# a list of FValues..
	request.session['activeIDs'] = activeIDs
	request.session.set_expiry(300) # 5 minutes ..	too much?


	context = {	  
		'user_is_logged_in' : request.user.is_authenticated(),
		'facetgroups_and_facets' :	 facetgroups_and_facets,			

		'ajaxflag' : DJF_AJAX,
		'twocolumnsflag' : DJ_2COLUMNS_INNERFACET,
		'splash_page' : DJF_SPLASHPAGE,

		'result_types' : RESULT_TYPES,	
		'result_typeObj' : FM_GLOBAL.get_resulttype_from_name(resulttype),	  
		'ordering' : ordering,

		'query_filtersBuffer' : [],
		'newurl_stub' : newurl_stub,
		}


	return ('djfacet/splash_page.html', context)








##################
#  
#  OLD STUFF 
#
##################



# view that collects the explanation strings for a given queryargs set
def explain_results(request):
	# global FM_GLOBAL
	FM_GLOBAL = access_fmglobal()

	# -------	
	# 2010-09-28: removed and made global...>>> fmanager = request.session.get('faceted_manager', False)
	queryargs = request.session.get('queryargs', False) 
	resulttype = request.GET.get( 'resulttype' )
	# -------

	expl_dict = FM_GLOBAL.explain_queryargs(queryargs, resulttype)

	context = {	  
		'expl_dict' :	 expl_dict, 
		'result_type' : FM_GLOBAL.get_resulttype_from_name(resulttype)['label'],		
		}

	return render_to_response('djfacet/components/explanation.html', 
								context, 
								context_instance=RequestContext(request))












# ajax function used to refresh the history panel..
def refresh_fbhistory(request):
	fsearch_history = request.session.get('fsearch', None)
	context = Context({ 'fsearch_history': fsearch_history }) 
	return_str = render_block_to_string('djfacet/faceted.html', 
										'inner_fsearch_history', 
										context)
	return HttpResponse("%s" % (return_str))



# function that makes sure that request.session['fsearch'] is kept up to date 
#  this dict is recognized in the template as 'fsearch_history' and it keeps a log of most recent 20 searches
# it should be in a context processor, but since the FB uses only ajax for now we've put it here...
def update_search_memory(fsearch_history, facetsGroup, active_facet, facetvalue):
	""" """
	newdict = {'group' : {'label' : facetsGroup.label, 'uniquename' :facetsGroup.uniquename} , 
				'facet' : {'name' : active_facet.name , 'uniquename' : active_facet.uniquename }, 
				'value': {'id' : facetvalue.id, 'displayname' : facetvalue.displayname }
				}

	if fsearch_history:
		flag = False  # routine to check for already existing triples
		temp = [facetsGroup.uniquename, active_facet.uniquename, facetvalue.id]

		for d in fsearch_history:
			if [d['group']['uniquename'], d['facet']['uniquename'], d['value']['id']] == temp:
				flag = True
		if not flag:
			fsearch_history.insert(0, newdict)
		if len(fsearch_history) > 20:
			fsearch_history.pop()
	else:
		fsearch_history = [newdict]

	return fsearch_history






