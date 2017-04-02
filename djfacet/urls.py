from django.conf.urls.defaults import *

from djfacet.constants import *

#faceted browsing application
urlpatterns = patterns('djfacet.views',
					   
	# main handler: eg .../djfacet/?filter=religionname_Christian&resulttype=country
	url(r'^$', 'home', name='djfacet_home'),
	
	# eg .../djfacet/allfacets/?resulttype=religions
	url(r'^allfacets/$', 'allfacets', name='allfacets'),
	
	# eg .../djfacet/facet/regionname/?resulttype=religions&totitems=
	url(r'^facet/(?P<facet_name>\w+)/$', 'singlefacet', name='singlefacet'),
	
	# ajax calls :
	# eg ..../djfacet/update_facet?filter=regionname_ArcticRegion&resulttype=religions&activefacet=regionname  TO CHECK
	url(r'^update_facet$', 'update_facet', name='update_facet'),
	
	
	# not used anymore
	# url(r'^update_results$', 'update_results', name='update_results'),	
	# url(r'^explain_results$', 'explain_results', name='explain_results'),
	# url(r'^refresh_fbhistory$', 'refresh_fbhistory', name='refresh_fbhistory'),
	# for logging
	# url(r'^log_query$', 'log_query', name='log_query'),
	# for testing 
	# url(r'^'+prefix+'faceted/info_item$', 'info_item', name='info_item'),
	# url(r'^'+prefix+'faceted/stuff$', 'stuff'),
)

