""" DJfacet_project settings.

originally coded by michele pasin on 2011-10-11
++++
A ``local_settings`` module must be made available to define sensitive
and highly installation-specific settings.

"""


import os, sys
import django
from time import strftime

# the site root is one level up from where settings.py is
DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))
SITE_ROOT = os.path.dirname(os.path.realpath(__file__)).rsplit('/', 1)[0]

sys.path.append(os.path.join(SITE_ROOT, "demoproject/apps"))
sys.path.append(os.path.join(SITE_ROOT, "demoproject/libs"))


# handy variable for setting up other parameters
LOCAL_SERVER, LIVE_SERVER = True, False


if not LIVE_SERVER:
	DEBUG = True
else:
	DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
	('mikele', 'michele@mail.com'),
)
MANAGERS = ADMINS 
TIME_ZONE = 'Europe/London'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True


MEDIA_URL = '/media/uploads/'
STATIC_URL = '/media/static/'
ADMIN_MEDIA_PREFIX = '/media/static/admin/'
MPTTEXTRA_ADMIN_MEDIA = '/media/static/feincms/'

# Absolute path to the directory that holds media uploaded
MEDIA_ROOT = os.path.join(SITE_ROOT, 'uploads')
# physical location of extra static files in development server
STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, 'demoproject/static'),
)
# path used with "python manage.py collectstatic"
STATIC_ROOT = os.path.join(SITE_ROOT, 'apache/static')



TEMPLATE_LOADERS = (
	# 'django.template.loaders.filesystem.load_template_source', DEPRECATED django1.3
	'django.template.loaders.filesystem.Loader',
	# 'django.template.loaders.app_directories.load_template_source', DEPRECATED django1.3
	'django.template.loaders.app_directories.Loader'
)


MIDDLEWARE_CLASSES = (
	'django.middleware.common.CommonMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	# tHis is deprecated, but needed here for backward compatibility in the admin
	'django.middleware.csrf.CsrfResponseMiddleware', 
)


TEMPLATE_DIRS = (
	os.path.join(SITE_ROOT, 'demoproject/mytemplates'),
)


TEMPLATE_CONTEXT_PROCESSORS = (
	"django.contrib.auth.context_processors.auth",
	"django.core.context_processors.debug",
	"django.core.context_processors.i18n",
	"django.core.context_processors.media" , 
	'django.contrib.messages.context_processors.messages',
	"django.core.context_processors.request",
	"django.core.context_processors.static"
)





ROOT_URLCONF = 'demoproject.urls'




INSTALLED_APPS = (	
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.humanize',
	'django.contrib.messages',
	
	'django.contrib.staticfiles',
	
	'django.contrib.admin',
	'django_extensions',
	 	
	'djfacet',	 
	'religions',

)






try:
	if LOCAL_SERVER:
		from local_settings import *
	elif LIVE_SERVER:
		from local_livsettings import *
except ImportError:
	pass






# 
# simple function that appends a debug string to another string (or file)
# 
def printdebug(stringa):
	""" helper function: print to the command line output only if not running WSGI (othersiwe it'd cause an error)"""
	if stringa == 'noise':
		stringa = "\n%s\n" % ("*&*^" * 100)
	if LOCAL_SERVER:
		print ">>[%s]debug>>: %s"  % (strftime("%Y-%m-%d %H:%M:%S"), stringa)
	else:
		pass







# ********
# SITE_WIDE CACHE
# ********

# Needed always cause the FB is stored here : from django.core.cache import cache

if LIVE_SERVER:
	CACHE_IS_LOADED = True	# False when testing or in other circumstances...
else:
	CACHE_IS_LOADED = False


if CACHE_IS_LOADED:
	MIDDLEWARE_CLASSES += ('django.middleware.cache.FetchFromCacheMiddleware',)   # CACHE: needs to be last
	temp = list(MIDDLEWARE_CLASSES)
	temp.reverse()
	temp += ['django.middleware.cache.UpdateCacheMiddleware']  # CACHE: needs to be first
	temp.reverse()
	MIDDLEWARE_CLASSES = tuple(temp)
	CACHE_BACKEND = 'locmem://'
	CACHE_MIDDLEWARE_SECONDS = 100000    #900
	if LIVE_SERVER:
		CACHE_MIDDLEWARE_ANONYMOUS_ONLY = False  # this makes sure that the admin is not cached
	else:
		CACHE_MIDDLEWARE_ANONYMOUS_ONLY = False



SESSION_COOKIE_AGE = 600 # 600  # 15 minutes


# ======= DJFACET options: showing all of them for description =======

DJF_CACHE = False   # default value = False
DJF_AJAX = False  	# default value = 'vertical' 
DJF_MAXRES_PAGE = 50  # default value = 50
DJF_MAXRES_FACET = 5  # default value = 5 
DJF_MAXRES_ALLFACETS = 9  # default value = 9 
DJF_SHOWLOGS = True		# default value = False
DJF_SPECS_MODULE = 'facetspecs'  # default value = 'facetspecs'
DJF_URL_AS_NUMBERS = False  # default value = False
DJF_SPLASHPAGE = True # default value = 'vertical'
DJF_SPLASHPAGE_CACHE = False  # default value = False
# DJF_STATIC_PATH = 'djfacet_beax'  # default value = 'djfacet'
DJF_MPTT_INHERITANCE = True  # default = False








