==+==

DJFACET: A faceted browser search engine built on top of Django. 

VERSION: 0.9.9.8

==+==

Django Faceted Browser is a Django application that allows you to navigate your data using an approach based on 'dynamic taxonomies', also called 'facets'.

This repository contains a Demo-project with a working installation of DJFacet. The 'religions' application will let you browse a sample dataset that describes the distribution of religions in the world. The database is provided as a sql dump.

The DJFacet engine itself can be found in the folder demoproject/apps/djfacet: https://bitbucket.org/magicrebirth/djfacet/src/tip/demoproject/apps/djfacet

This is what you need to include in your own project if you want to use the djfacet app.

-----------------------------------------

Source code and issue tracking: 
https://bitbucket.org/magicrebirth/djfacet/

Demo: 
http://demos.michelepasin.org/djfacet/

Online Documentation (in progress): 
http://www.michelepasin.org/support/djfacet/docs/





===============
=============
RUNNING the DEMO project
=============
===============



LOADING THE DEMO DATABASE ('RELIGIONS' APP):
...........................................
In ../demoproject/db there is a MySQL dump of the database used by the 'religions' app. 
Import that into the database associated to your Django installation. 


UPDATING LOCAL_SETTINGS.PY:
..................
Update the DATABASES dictionary so that the demo database can be accessed. 


RUN THE APPLICATION
...........................................................
That's it.. now you should be able to run the app as usual:
python manage.py runserver 

To access the admin login as (administrator account): 
usr: test / psw: test 

DJFacet is mounted on:
http://127.0.0.1:8000/djfacet/






===============
=============
CHANGELOGS
=============
===============


2012-08-08
-----------------------------------------
- added support for number-based facets
	- in specs: 'range_interval' : 10000000,
- fixed small bug in queryhelper, when caching from console
- modified the docs for intro a little...



2012-06-15
-----------------------------------------
- fixed bug with non unicode values in cache_manager.py
- separated breadcrumbs into its own template



2012-06-08
-----------------------------------------
- single_facet.html
	- removed the group name from breadcrumbs
	- changed text for in-between-searches views: 'search results' rather than 'all'
- snippet_facet
	- on splash_page, the 'more' links is always active
	- with mptt facets, the 'more' links is always active 
- queryhelper: changed queries so to include values with count = totnumber_results
- facet.py: fixed bugs on recursive_tree_forfacetvalue
- single_facet.html: separated out the breadcrumbs sectino into control_breadcrumbs.html



2012-05-30
-----------------------------------------
* modified history: 
	most recent items never shown as it's what's alteady displayed!
* added jquery libraries to projects
	- modified base.html



2012-05-29
-----------------------------------------
* added DJF_HISTORY_SIZE parameter
* added little script for cleaning the session periodically
* added robots.txt
* simplified LOCAL_SERVER, LIVE_SERVER routine in settings.py
* updated CSS (added open-close icons, help icons)
* updated js for openclose behaviour
* facetedbrowser.html: removed controls_selected 
* control-bar.html: updated the way selected facet values are presented
* single-facet: updated breadcrumbds rendering



2012-05-23
-----------------------------------------
* fixed bug that prevented mptt hierarchy navigation when using cached values
	- added <mpttsubs> field to CachedFacetValue model
	- added handling of <showonly_subs> when calling cache_manager from fmmanager
	- added handling of <showonly_subs> when calling <getCachedFacetValues> in cache_manager
* removed the <djfacet_cleanfacetcache.py>
	- now the <djfacet_facetcache> command also has a 'reset' method
* cache_manager: renamed _cacheOneFacetValue method to _cacheOneFacet
* updated readme with info on how to set up the demo app
* updated <djfacet_fmcache> command:
	- now it wipes out everything was cached beforehand, before caching the new FM
* fixed bug in queryhelper>modify_countarg_forMPTT
* started separating the facetspecs in a more rational way:
	- 'mptt' : True is at the too level
	- modified all demo-facetspecs
* queryhelper>_calcvaluesForStandardQueries
	fixed bug that prevented the totCount of valid values to be corrent
* added UI blocking to djfacet.js
* updated _calcvaluesForStandardQueries: 
	- when DJF_MPTT_INHERITANCE=False vals with 0 results are eliminated 
* updated _calcMPTT_inheritance
	- added missing code for already exploded mptt values
* updated error messages in constants.py (facetspecs loading routine)
* facetgroup>buildfacets_fromspecs: 
	added 'active' to facetspecs definition - quick way to deactive a facet - defaults to True.






2012-05-18
-----------------------------------------
* added support for AJAX facets update, via the DJF_AJAX constant
	- blockUI behaviour is functioning, but is not used yet






2012-05-17
-----------------------------------------
* added a history mechanism 
	- works with both searches and single_records views
* simplified the result-type selection-UI links
	- unified use of control_bar template across entire site
* single item template: added support for prev/next navigation
* separated out the single-item view from the main search one
* moved all results-related templates into /results folder



2012-05-16
-----------------------------------------
* added tree info also on 'control_selected' panel on facetsearch page
	- parents can be clicked on for a new search
* formatted the no results page:
	http://127.0.0.1:8000/djfacet/?resulttype=religions&filter=religionname_Christian&filter=religionname_other
* single-facet: now shows father information too
* http://127.0.0.1:8000/djfacet/?filter=religionname_ChurchofGod&resulttype=country&filter=religionname_Bah%C3%A1%27%C3%ADFaith
	- unicode error deriving from filtersBuffer
	==> FIXED via using 'force_unicode' instead of 'str' in all queryargs-explosion routines
* site.css: added .activeFilter class for selected filters formatting
* http://127.0.0.1:8000/djfacet/facet/religionname/?resulttype=country&totitems=82&filter=religionname_Christian
	- Does this work? Somtimes it seems to fail..? 
	- Apparently it does work.. [??]
- single facet view is now ordered alphabetically!	
	==> FIXED via new templateTag: fvlist_formatter2
* http://127.0.0.1:8000/djfacet/facet/religionname/?filter=religionname_Christian&resulttype=country&ordering=&showsubs=religionname_Christian&totitems=82
	show only subs works the first time only--why?
	- problem with URL-stub creation mechanism? 
	- eg try to click on church of england. some funny results will come up...
	==> FIXED by checking for showonly_subs flag also when creating the valid_values list
* http://127.0.0.1:8000/djfacet/?filter=religionname_other&resulttype=country&filter=regionname_Africa
	- religion should show other options but it doesn't
	- seems that it limits to sub-concepts of 'kimbanguist'
	- in general we need to let m2m relations work over mptt fields (opposite to what happens on Flamenco)
	==> FIXED through the new mptt routine 
* http://127.0.0.1:8000/djfacet/?filter=religionname_other&resulttype=country&filter=regionname_Africa
	after adding Religion name: other (with Africa loaded) the religions are not shown?
	- activeIDs not updated? ==> FIXED through the new counting routine
* added <get_MPTTroot> method to facet
* hidden MPTT facetvalues with count != tot current results set
* added 'showsubs' url parameter in single_facet
	- separates views of descendants-only, from queries that show facetvalues from all trees
	- In QueryHelper, <_validateMPTTvalue> updated so that it keeps only the top-level items
* simplified <_inner_runquery> when using MPTT facets
http://127.0.0.1:8000/djfacet/?resulttype=religions&filter=religionname_ChurchofGodinJamaica
	- too many results are returned
	- the query approach based on tree_id fails, because other branches of the tree gets included too!
		>>> Religion.objects.filter(tree_id=r2.tree_id, level__gt=r2.level)
	- new approach: extract all descendants IDs and include those in the query
* modified snippet facet so that it still shows the facet box when there are no filters available



2012-05-14
-----------------------------------------
* added basic mechanism for zooming into facetvalues from single_facet page
* http://127.0.0.1:8000/djfacet/allfacets/?resulttype=religions
	- count of Christians is +2 of the real one..
	- i think whats happening is that since we count based on dbfield-name, items such 'batpist' end up being counted twice since they apper
	in two different trees..
	- FIXED by counting mptt facetvalues based on ID, not dbfield (=name stated in facetspecs) 
* added tree_id info to facetvalues, via the 'mptt_treeID' property
* http://127.0.0.1:8000/djfacet/?filter=religionname_Catholic&resulttype=country
	- count for catholics is wrong (141 versus 134) ?
	- the issue should be that in counting subconcepts separately, duplicates end up in the final count...
	==> seems to be FIXED: now there are some issues with the new algorithm, but in general it works...
* added djfacet/components/history.html (as a placeholder for the moment)
* added 'control_bar.html' component
	- displays current result type and links to other ones available
* finalized first stable version of query mechanism for hierachical facets (via MPTT)
* site.css:
	.splashPage .minHeight changed to accommodate facets with more values
* added mechanism in __validateQueryFilters for eliminating MPTT filters that are 'father'
	- eg when one of their children is already in the query
* fixed routine in <_inner_runquery> for queries involving MPTT facetvalues



2012-04-26
-----------------------------------------
* updated demo DB: all religion names with parenthesis eliminated
* added mechanisms for MPTT when extracting available facetvalues
	- showing only top level ones depending on current query
* added subspreview attribute to facetvalues, usable to add tooltip with subtypes in template
	- modified templates single_facet and snippet_facet so that they accept tooltips
* in QueryHelper eliminated all_values_flag, which is now inferred directly from queryargs 
	- simplified the routine for DISTINCT
* added DJF_MPTT_INHERITANCE setting option
* fixed bug that prevented single_facet pages to be loaded at any time, via the URL-query
	- in facetedmanager>>refresh_facetvalues, activeIDs were not recalculated if missing
* added MPTT admin view for Religions
* added a new constant, <DJF_STATIC_PATH> that defaults to 'djfacet' and lets you
 	- modify the static files without having to change the default package
	- it's enough to set the var name to the folder you create in STATIC_DIRS
* fixed bug in <fvlist_formatter1> template tag
* fixed a bug that prevented the the facetvalues pagination to happen when using the cache





2012-03-02
-----------------------------------------
* cleaned up templates
* upgraded to 'staticfiles' app for handling static files
* improved explicative text on 'single_facet' template when filters are present





2012-03-01
-----------------------------------------
- second-level show-all facet-values page: 
	- disabled links that have totresults number = to current results number
	- (this prevents case in which the same value gets clicked twice too)
	- updated tooltips too
- separated templates for footer and navbar
- changed the prefix of all constant names
 	- DJ_.... ====> DJF_....
- facetvalues previews are now calculated more precisely (the 'see more' button is dynamically created) 
	- modified the FM.refresh_facetvalues(LIMIT=...) call
		- modified the QueryHelper.calculate_facetvalues() function
			- changed it for standard queries: _calcvaluesForStandardQueries
			- changed it for or queries: _calcvaluesForORQueries  [UNTESTED THOUGH]

		- each facetvalue instance has now 3 new attributes: 
			- fv_copy.tot_left = remaining_values
			- fv_copy.tot_inbatch = tot_limitvalues
			- fv_copy.tot_all = tot_allvalues
- updated and simplified the 'snippet_facet' template
- added a dump of the religions DB



2012-02-29
-----------------------------------------
- implemented the two-screens (show_all) interaction on search page too
- set the cache time to a much lower value - maybe I'll solve the cache problem!
	cache.set('DJ_FM_GLOBAL', FM_GLOBAL, 10000)
- removed the <get_facetsForTemplate> routine in views.py
- added all the colors to templates "red" "gray" "green" "purple" "blue" "brown"
- fixed bug: when querying for non-existing values, or switching resType thus causing non allowed facets to be in the query, the query wasn't redirected correctly.



2012-01-12
-----------------------------------------
* cleaned up the data in sample database
	- a new religions.json file added to the religions app in /fixtures


2012-01-11
-----------------------------------------
* addded <snippet_respagination.html>
* removed the DJ_2COLUMNS_INNERFACET parameter and associated logic in views.py
	- the splitting of lists is done in templates, as it should be cause it's presentation logic!
* added a templatetag for formatting fvalues in single_facet.html
* removed the registration app 
* renamed <fb_tags> into <djf_tags>
* started adding the new html5 templates
	- single_facet.html
	- all_facets.html
	- facetedbrowser.html

2012-01-09
-----------------------------------------
Added the demo project that embeds the Djfacet app.
Other things:
* added an /index.html to the demo webapp
	- includes a dynamic preview of djfacet parameters
* added a Demo project that includes Djfacet
* added the cursor.close() command on fmanager



2011-11-08
-----------------------------------------
* updated <snippet_facet2cols> so that it shows the 'show all' button on second column only
- removed 'count_is_active' var from all templates
* if on facet/name/ we switch resType but it doesn't exist, it breaks [FIXED]
* moved <access_fmglobal> to facetedmanager.py in order to avoid conflicts! 
* updated and tested command <djfacet_cleanfacetcache>
* updated and tested command <djfacet_cleanhtmlcache>
* updated and tested command <djfacet_facetcache>
	- added an option that allows caching also the fm object 
* updated and tested command <djfacet_shell>
* updated and tested command <djfacet_fmcache>
- removed DJFACET_TEST constant
* fixed the django's db_type deprecation warning (by passing the connection obj)
	- https://docs.djangoproject.com/en/dev/howto/custom-model-fields/#django.db.models.Field.db_type
* modified: access_fmglobal(FORCE_CREATION=False)
	added the FORCE_CREATION flag
* renamed <djfacet_store_facetmanager> into <djfacet_fmcache>





2011-11-04
-----------------------------------------
* added LIMIT methods for getting only a subset of the facet values
	- adding slicing shouldnt influence the query too badly..
	- https://docs.djangoproject.com/en/dev/topics/db/queries/#limiting-querysets
	- modified fucntions to pass the LIMIT parameter: 
		- views.py, facetedmanager/refresh_facetvalues, and then in <queryhelper/calculate_facetvalues>
* modified the splash page so that it accommodates linkes to the 'single_facet/all' views
	- works only on splash page now; also, it's hard-coded, doesn't really check if the ones displayed are all the facets or not!
* optimized the facet-all page...
* added constant <DJF_MAXRES_FACET>
* moved a bunch of functions from /views.py to fb_utils/utils.py
* copied all the latest stuff from POMS
* fixed the command <djfacet_cleanhtmlcache>
* added the <delete_cachedHTMLpage> method for cleaning cached html pages
* renamed cache_db into <cache_manager>
	- moved the cacheHTML methods in there..
* simplified splash_page construction
* removed a bunch of old stuff: <unused.py>
* cleaned up <determine_ordering>
* changed name of flag for splash page in template: djfacet_splashpage
* cache_ram module has been removed
* added cacheHTMLpage methods to <cache_db.py>
* removed DJF_SPLASHPAGE_ORIENTATION; now DJF_SPLASHPAGE can be 'horizontal', 'vertical' or False (= no splash page)
* renamed "_facetspects" into "facetspecs_example" 
* rationalized all the templates
* I removed all the non-overridden templates from the application folder (mytemplates)
	- much cleaner now
- moved everything to /bitbucket





2011-09-05
-----------------------------------------

- removed white spaces from url filters
- removed DJFACET_COUNT constant
- simplified facetviews/get_facetsForTemplate
- removed <cache_ram>
- added DJF_SPLASHPAGE constant: defaults to True, indicate that we want the facets-only splash page
- added <djfacet_splash.css> and if statements on base.html
- added 'DJF_SPLASHPAGE_ORIENTATION' constant (horizontal or vertical)
	- parameter still not available..
- added DOCS folder with sphinx documentation
	
- DOCs: added mention of URLS.py setup
	
- fixed bug: facetviews/update_results, added 'if x'
	- query_filtersBufferIDs = [str(x.id) for x in query_filtersBuffer if x]

- added optional representation of facet values as strings:
	- constats.py DJF_URL_AS_NUMBERS = False
	- facetvalue.py <__constructID>
	- facet.py <get_facetvalue_from_id>
	- facetviews.py: removed the int() whenever that was used, eg:
		- eg: facetvalue = FM_GLOBAL.get_facetvalue_from_id(fvalue_id)

- RAMcache eliminated for now
- LTB references in the orderings.py file are removed
	- but the elements in the dictionary are still there...
- started refining DJFacet test directly here
- changed 'TOT' to 'tot.'
- added bkcolors to facet groups, and default ones
	- added SOFT_HTML_COLORS constant
	- updated the FacetGroup class, and facetviews.py creation script





2011-05-31
-----------------------------------------

- separated out DJFacet app in my local copy, from the test application
- DJFACET_COUNT = True by default
- DB: countries have duplicated associated religions!!!!! 
	- removed through a script
- added possibility of viewing single items
	- embedded in the normal FB search logic
		- really cool!
	- added table views for single items
- added some logic for template selection, depending on folders/html files available
- separated out result list table with different template "results_list_table.html"
- separated out result list items with different template "results_list_items.html"
- polished up the religions db and make a dump
	- added SqlLite for testing, and fixtures
- added basic stub for ordering behaviour
	- tailored to LTB, but should be made more generic...
- facetviews: in 'get_facetsForTemplate' added logic for handling DJ_2COLUMNS_INNERFACET
	- list of values is split when necessary...
- updated 'facets_list': added logic that handles the creation of facets
	- for ajax and two columns situations
	- makes use of the snippets directly, doesn't replicate code
- updated the 'snippet_facet' and 'snippet_facet2Columns' templates
- added new constant: DJ_2COLUMNS_INNERFACET
	- defaults to False, serves to use the 2 columns template
- fixed a unicode error when creating the ID of the facetvalue
- commented out the 'from religions.models import *' from facetviews
	- it must be application independent!
- fixed problem with SVN
- UI: provideed support for ajax queries
	- through a separate template, loaded if DJF_AJAX is set to True






2011-04-22
-----------------------------------------

- changed the ID mechanism for facets in UI
	- now the ID is the 'uniquename'
		- avoids the problem of id(object) changing...
	- do we still need ID in facet-objects? 
- made the djfacet folder external in my local repository
	- removed it from SVN (it's still there as part of the test project though!)
- started working on the AJAX calls
	- added djfacet.js (set the AJAX constant to true to run it)
	- fixed problem with accordion css [added fillSpace: true]
- added the 'update_facet' function, still unfinished
- finished modularizing the templates
- fixed problem with symlinks (they don't get created via Dropbox, nor SVN)
	- so when updating from one computer to another it just copies the whole thing!!!
- created SYMLINKS from djfacet app /templates and /static to the actual tempaltes and media locations
	- this way we can just copy the djfacet application to move it!
	- the location of templates (/djfacet) remains the same
	- the location of media has been changed (/css... => /djfacet/css....)
- created SYMLINKS from djfacet app to the app in djfacet_test_project
	- so now we can update it only in one place!
- fixed bloody error with session expiry time
	- I had to set the queryargs list to Null in order to reload it
- started modularizing the templates
	- eg we provide some default ones, that can be overridden!
- removed 'demo-site' text there are no results..





2011-04-12
-----------------------------------------
- added response-redirect behaviour for queries with invalid IDs
- added feature: if a resulttype in specs.behaviour is not specified:
	- don't show that facet there!
	- this should let us do this (dynamically choosing facets) : 
		- looking at religions, it makes sense to have a country-name facet
		- looking at countries, it doesn't
			- so we want to have a country-initials facet
	- changed also the interface-creation routine
		- facets are result-type-specific!
- made the specs file external (at root level!)
	- can be customized using the 'DJF_SPECS_MODULE' setting (defaults to 'facetspecs')





6/4/11
-----------------------------------------

- updated and tested 'fb_store_facetmanager' and 'fb_createcache'
	- cache mechanism work fine 
- simplified the QueryCaching system: 
	- changed'optimize_query' method 
	- removed one table [CachedQueryArgs] from the DB/models
	- now the args are in a TextField in CachedFacetQuery
		- will it be fast enough?
- started refactoring the queryargs algorithm
	- now queryargs are a list of facetvalues (since each of them is unique)
	- also: refactor the 'refresh_facetvalues' method
- prob: if I hit the back button and then reload the page, something fails
	- FIXED: it was about updating the Buffer as needed
- removed 'action' from query string
	- it's calculated at runtime depending on difference between args <-> bufferArgs
- added a div for facetgroup in faceted.html
- added a scrollable panel for facets lists






5/4/11
-----------------------------------------

- changed the dir structure for googlecode
	- djfacet is temporarily empty!
- substituted 'printdebug' with 'djfacetlog'
	- controllable via a settings variable: DJF_SHOWLOGS (defaults to True)
- make pickleobject internal to FB
	- how easy to do? can we just reuse a recipy from djsnipppets? 
	- or we leave it outside? it's not just one file...
		- for the mom let's leave it as it is: we need to do some testing on performance too!
- made modelextra fields/models (=timestampedHidden model) internal to FB
	- removed the 'utils' package from the root level for this demo!
- added a mechanisms that loads FB settings; if not present assigns them default values
	- done in djfacet.constants.py 
- made the ID representation of facetvalues deterministic 
	-> so that different runs of FM will keep consistence!
	- IDs are a bit longish.. but for now that'll do
- added 'isdefault' : True to resultType specs
- there is a problem when switching result type.. url is not maintained correctly!
	- fixed
- eliminated the 'view all results' page (difference between 'all' and 'reset' commands)
- if I reload twice a page with same URL, the filter is applied twice (but it shouldn't)
	- fixed by checking for same-id filters
- separated all the dynamic stuff (faceted.html) from static (base.html)
-added an initial & char to the url_stub stringa
- starter refactoring the FBviews code for non-ajax capabilities
	- big change: queryargs can be represented through values IDs only!
		- we can infer the group and facet from it.. because each value gets a unique ID
	- added a method: get_facetvalue_from_id at the FM level
- added the propertly 'group' to a facet
	- this way from a facet we can go back to groups!
		- now it's doesn't really make sense to add a facet to multiple groups..rght?
		- TODO: fix the specs definition
- added a method 'result_typesObjCopy' in facetviews
	- allows to slim down the resType obj so to pass it to the browser entirely
		- we found out it wasn't really needed.. but whatever
- start adding the FB behaviour, managed to load and display
	- created a basic html template for the FB
	- removed all the unnecessary stuff!
- started making all utils internal to FB, for better portability
- sample DB and schema from 
	http://www.mysqltutorial.org/mysql-sample-database.aspx
		- fuck it's too complex to reuse it!
	- just create a new one ... I created a DB: djfacet_test
		- now need to fill it up with something..!
- second try: maybe add publications/people?
	- persons author publications (m2m through)
	- publications have types (fk)
	- persons work in projects (m2m)
	- projects produce softwares (m2m)
	- persons work for a university (fk)
- third try (implemented)
	- religions from an online datasets
	- the data need to be polished up a bit, but in general it's fine


