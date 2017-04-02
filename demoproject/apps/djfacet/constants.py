
from django.conf import settings


if hasattr(settings, 'DJF_CACHE'):
	DJF_CACHE = settings.DJF_CACHE
else:
	DJF_CACHE = False

# 2011-09-05: eliminated	
# if hasattr(settings, 'DJFACET_COUNT'):
#	DJFACET_COUNT = settings.DJFACET_COUNT
# else:
#	DJFACET_COUNT = True	
	
# 2011-11-07: eliminated	
# if hasattr(settings, 'DJFACET_TEST'):
#	DJFACET_TEST = settings.DJFACET_TEST
# else:
#	DJFACET_TEST = False
# 
#	

if hasattr(settings, 'DJF_AJAX'):
	DJF_AJAX = settings.DJF_AJAX
else:
	DJF_AJAX = False	
	
	
if hasattr(settings, 'DJF_MAXRES_PAGE'):
	DJF_MAXRES_PAGE = settings.DJF_MAXRES_PAGE
else:
	DJF_MAXRES_PAGE = 50	


if hasattr(settings, 'DJF_MAXRES_FACET'):
	DJF_MAXRES_FACET = settings.DJF_MAXRES_FACET
else:
	DJF_MAXRES_FACET = 5


if hasattr(settings, 'DJF_MAXRES_FACET'):
	DJF_MAXRES_ALLFACETS = settings.DJF_MAXRES_ALLFACETS
else:
	DJF_MAXRES_ALLFACETS = 10



if hasattr(settings, 'DJF_SHOWLOGS'):
	DJF_SHOWLOGS = settings.DJF_SHOWLOGS
else:
	DJF_SHOWLOGS = False



if hasattr(settings, 'DJF_SPECS_MODULE'):
	DJF_SPECS_MODULE = settings.DJF_SPECS_MODULE
else:
	DJF_SPECS_MODULE = 'facetspecs'



if hasattr(settings, 'DJF_URL_AS_NUMBERS'):
	DJF_URL_AS_NUMBERS = settings.DJF_URL_AS_NUMBERS
else:
	DJF_URL_AS_NUMBERS = False


if hasattr(settings, 'DJF_STATIC_PATH'):
	DJF_STATIC_PATH = settings.DJF_STATIC_PATH
else:
	DJF_STATIC_PATH = 'djfacet'



if hasattr(settings, 'DJF_SPLASHPAGE'):
	if settings.DJF_SPLASHPAGE in ['horizontal', 'vertical', False]:
		DJF_SPLASHPAGE = settings.DJF_SPLASHPAGE
	else:
		DJF_SPLASHPAGE = 'vertical'
else:
	DJF_SPLASHPAGE = 'vertical'
	
# 
# if hasattr(settings, 'DJF_SPLASHPAGE'):
#	DJF_SPLASHPAGE = settings.DJF_SPLASHPAGE
# else:
#	DJF_SPLASHPAGE = True
# 
# 
# 
# if hasattr(settings, 'DJF_SPLASHPAGE_ORIENTATION'):
#	if settings.DJF_SPLASHPAGE_ORIENTATION in ['horizontal', 'vertical']:
#		DJF_SPLASHPAGE_ORIENTATION = settings.DJF_SPLASHPAGE_ORIENTATION
# else:
#	DJF_SPLASHPAGE_ORIENTATION = 'vertical'
# 


if hasattr(settings, 'DJF_SPLASHPAGE_CACHE'):
	DJF_SPLASHPAGE_CACHE = settings.DJF_SPLASHPAGE_CACHE
else:
	DJF_SPLASHPAGE_CACHE = False


if hasattr(settings, 'DJF_MPTT_INHERITANCE'):
	DJF_MPTT_INHERITANCE = settings.DJF_MPTT_INHERITANCE
else:
	DJF_MPTT_INHERITANCE = False


if hasattr(settings, 'DJF_HISTORY_SIZE'):
	DJF_HISTORY_SIZE = settings.DJF_HISTORY_SIZE
else:
	DJF_HISTORY_SIZE = 15



import os
try:
	specs_location = os.environ['DJANGO_SETTINGS_MODULE'].split('.')[0] + '.' + DJF_SPECS_MODULE 
except:
	raise Exception("DJFACET: Can't load the os.environ['DJANGO_SETTINGS_MODULE'] in 'Constants.py.....'")
	raise
try:
	DJF_SPECS = __import__(specs_location, globals(), locals(), [''])
except SyntaxError, e:
	import traceback
	top = traceback.extract_stack()[-1]
	t = ", ".join([type(e).__name__, os.path.basename(top[0]), str(top[1])])
	raise Exception("\n\n***** DJ_FACET: syntax error in <%s> file.. \n===>%s\n\n" % (specs_location, t))	
except Exception, e:
	import traceback
	top = traceback.extract_stack()[-1]
	t = ", ".join([type(e).__name__, os.path.basename(top[0]), str(top[1])])
	raise Exception("\n\n***** DJ_FACET: error with <%s> file.. Is it available at rhe root level of your django project? \n===> http://www.michelepasin.org/support/djfacet/docs/configuration.html\nPython error: %s\n" % (specs_location, t))




# THIS WORKS TOO, BUT SEEMS LESS PORTABLE
# import facetspecs as SPECS






# http://www.myhtmltutorials.com/softcolor.html

SOFT_HTML_COLORS = ( "EEFFFF", "FFEEFF" , "FFFFEE", "EEEEEE" ,"EEFFEE" , "FFEEEE" , "DDEEEE" ,	"EEDDEE",	"EEEEDD", "DDDDEE", "DDEEDD","EEDDDD",	"DDFFFF",	"FFDDFF",	"FFFFDD", "DDDDFF", "DDFFDD",	"FFDDDD", "CCDDDD", "DDCCDD", "DDDDDD" ,  "EEEEFF", "DDDDCC", "CCCCDD", "CCDDCC",	"DDCCCC", "CCEEEE", "EECCEE",	"EEEECC", "CCCCEE", "CCEECC",	"EECCCC" ,"CCFFFF", "FFCCFF",	"FFFFCC" ,"CCCCFF", "CCFFCC",	"FFCCCC")


# SOFT_HTML_COLORS = ( "red", "green" )





