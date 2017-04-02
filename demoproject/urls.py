from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template

import djfacet.constants as DJ_CONSTANTS
prefix = settings.URL_PREFIX
parameters_peek = [(x,getattr(DJ_CONSTANTS, x)) for x in dir(DJ_CONSTANTS) if x.startswith("DJ")]
parameters_names = [x for x in dir(DJ_CONSTANTS) if x.startswith("DJ")]
parameters_values = [getattr(DJ_CONSTANTS, x) for x in dir(DJ_CONSTANTS) if x.startswith("DJ")]



urlpatterns = patterns('',)	 # init


if not settings.LIVE_SERVER:
	from django.contrib import admin
	admin.autodiscover()

	urlpatterns += patterns('', 
		# standard admin urls	
		(r'^'+prefix+'admin/', include(admin.site.urls) ),			 

		)


# standard urls
urlpatterns += patterns('',
	# the home page: eventually we can add a list of apps....
	(r'^'+prefix+'$', direct_to_template, {'template': 'index.html', 
											'extra_context' : {'parameters_peek' : parameters_peek} }),
	(r'^'+prefix+'robots.txt$', direct_to_template, {'template': 'robots.txt',}),
	# DJFacet app
	(r'^'+prefix+'djfacet/', include('djfacet.urls') ),

)





if settings.LOCAL_SERVER:     # ===> static files on local machine
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns('',
        (r'^media/uploads/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        )




