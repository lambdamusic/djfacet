from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from django.conf import settings
from django.db import connection, models
from time import strftime
import time
import cPickle

# from _commandsimports import *
from djfacet.load_all import *


##################
#  
#  Command that creates the cached version of the faceted manager.
# 
# 	By default it also erases all previously cached values.
#
##################


# EG:
# bash-3.2$ python manage.py djfacet_fmcache



class Command(BaseCommand):
	args = '<no args>'
	help = 'Saves the faceted manager instance in the database, using pickle'

	# make_option requires options in optparse format
	# option_list = BaseCommand.option_list	 + (
	#			  )


	def handle(self, *args, **options): 
		"""
		args - 
		options - 
		"""

		# feedback:
		print "\n++ = ++ = ++ = ++ ++\n%s\nSTARTING CACHING the Faceted Manager using pickle"	 % strftime("%Y-%m-%d %H:%M:%S")	
		print "++ = ++ = ++ = ++ \n"
		
		print "++ = ++ = ++ = ++ Cleaning all previously cached contents (fmanager & values)...."
		CachedFacetedManager.objects.all().delete()  # empty it first: there must be one line only
		CachedFacetQuery.objects.all().delete()
		CachedFacetValue.objects.all().delete()
		
		#  IF YOU PASS FORCE_CREATION=True then the FM IS RECONSTRUCTED		
		FM_INSTANCE = access_fmglobal(FORCE_CREATION=True)

		c = CachedFacetedManager(manager=FM_INSTANCE)
		c.save()
		
						
		print '.........successfully cached the Faceted Manager object!\n'
