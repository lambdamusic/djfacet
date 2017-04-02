from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from django.conf import settings
from django.db import connection, models
from time import strftime
import time

from djfacet.load_all import *




# EG:
# bash-3.2$ python manage.py djfacet_cleanhtmlcache 



class Command(BaseCommand):
	args = '<pagename>'
	help = 'Delete CachedHtmlPage objects so that it gets re-calculated'

	# :an init method that does the repetitive stuff....
	def __init__(self, *args, **kwargs):

		super(Command, self).__init__(*args, **kwargs)
	


	def handle(self, *args, **options): 
		"""
		args - args (eg. myapp in "manage.py reset myapp") = the facet names [result types are all by default]
		options - configurable command line options
		"""
	
		if args:
			temp = []
			for a in args:
				djfacetlog("Argument provided: ==%s== [NOT IMPLEMETED YET]" % str(a))
	
	
		n = CachedHtmlPage.objects.all().count()
		CachedHtmlPage.objects.all().delete()
		

		# feedback:
		print "\n\n++ = ++ = ++ = ++ = ++ = ++ = ++ = ++\nCACHED HTML PAGES DELETED: %d \nIf 'DJF_SPLASHPAGE_CACHE' is set to True the all-facets page will be cached again automatically the first time they're loaded." % n
		print "++ = ++ = ++ = ++ = ++ = ++ = ++ = ++\n"

