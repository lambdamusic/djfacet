from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from django.conf import settings
from django.db import connection, models
from time import strftime
import time

from djfacet.load_all import *


##################
#  Tue Sep 14 15:29:58 CEST 2010
#	
#
##################



# EG:
# bash-3.2$ python manage.py djfacet_facetcache
# bash-3.2$ python manage.py djfacet_facetcache --fmcache=yes   # force cache also the FM object
# bash-3.2$ python manage.py djfacet_facetcache gender
# bash-3.2$ python manage.py djfacet_facetcache gender --secondlevel=yes  --lowerlimit=9905
# bash-3.2$ python manage.py djfacet_facetcache possoffice possunfreepersons posslands possrevkind possrevsilver privileges


# bash-3.2$ python manage.py djfacet_facetcache --reset=yes  # clears everything
# bash-3.2$ python manage.py djfacet_facetcache --emptyunused=yes  # removes only unusued values


class Command(BaseCommand):
	args = '<facet_uniquename1, facet_uniquename2, facet_uniquename3 etc. >'
	help = 'Cached all facet values within the facets available'

	# make_option requires options in optparse format
	option_list = BaseCommand.option_list  + (
						make_option('--resulttypes', action='store', dest='resulttypes', 
									default='all', help='The _resulttypes_ option determines what resulttypes-facet couple will be cached'),
						make_option('--enforce', action='store', dest='enforce', 
									default='yes', help='The _enforce_ option determines whether we delete previously cached object (default= TRUE!)'),
						make_option('--onlyrescounts', action='store', dest='onlyrescounts', 
									default='no', help='The _onlyrescounts_ option determines whether to update only the res tot-counts (no facet values)'),
						make_option('--fmcache', action='store', dest='fmcache', 
									default='no', help='The _fmcache_ option determines whether to recache the faceted manager instance too'),
						# DELETING STUFF			
						make_option('--emptyunused', action='store', dest='emptyunused', default='no',
									help='The _emptyunused_ option empties the unused elements from CachedFacetValue and CachedQueryArgs tables'),
						make_option('--reset', action='store', dest='reset', default='no',
									help='The _reset_ option removes all previously cached values in the DB (also the FM)'),

				  )


	# :an init method that does the repetitive stuff....
	def __init__(self, *args, **kwargs):
		

		super(Command, self).__init__(*args, **kwargs)



	def handle(self, *args, **options): 
		"""
		args - args (eg. myapp in "manage.py reset myapp") = the facet names [result types ...]
		options - configurable command line options
		"""


		# delete section
		if options['emptyunused'] == 'yes' or options['reset'] == 'yes':
			if options['emptyunused'] == 'yes':
				self.fm = access_fmglobal()
				cacheDBinstance = DbCache(self.fm)
				print '.... now deleting all the unused elements...'
				tot = cacheDBinstance._emptyUnusedElements()
				print '............. successfully deleted [%d] unused elements' % tot
			elif options['reset'] == 'yes':
				print "++ = ++ = ++ = ++ Cleaning all previously cached contents database...."
				CachedFacetedManager.objects.all().delete()  # empty it first: there must be one line only
				CachedFacetQuery.objects.all().delete()
				CachedFacetValue.objects.all().delete()
				print '.........successfully erased all previously cached contents!\n'
				
			
		else:

			if options['enforce'] == 'yes':
				ENFORCE = True
			else:
				ENFORCE = True	# to be implemented..
			
			if options['fmcache'] == 'yes':
			
				# CLEAN UP AND RECONSTRUCT THE CACHED FM INSTANCE  
			
				print "++ = ++ = ++ = ++ Cleaning all previously cached contents database...."
				CachedFacetedManager.objects.all().delete()  # empty it first: there must be one line only
				CachedFacetQuery.objects.all().delete()
				CachedFacetValue.objects.all().delete()
				FM_INSTANCE = access_fmglobal(FORCE_CREATION=True)
				c = CachedFacetedManager(manager=FM_INSTANCE)
				c.save()
				print '.........successfully cached the Faceted Manager object!\n'
				FM_INSTANCE.init_resulttypes_activeIDs()
			
			else:						
			
				#  USED WHATEVER CACHED VERSION OF THE FM IS AVAILABLE (PS: <DJF_CACHE> MUST BE SET TO TRUE )
				#  ALTERNATIVELY, access_fmglobal() WILL RE-CREATE THE FM BUT WILL NOT CACHE IT 
			
				FM_INSTANCE = access_fmglobal()
				FM_INSTANCE.init_resulttypes_activeIDs()	 #cache this in memory first.


			
			all_facets = FM_INSTANCE.get_all_facets()
			all_resulttypes = FM_INSTANCE.result_types

			
			if args:
				temp = []
				for a in args:
					djfacetlog("Argument provided: ==%s==" % str(a), True)
					temp += [x for x in all_facets if x.uniquename == str(a)]
				all_facets = temp

			if options['resulttypes'] != 'all':
				test = FM_INSTANCE.get_resulttype_from_name(options['resulttypes'])
				if test:
					all_resulttypes = [test]
				else:
					raise Exception, "ERROR: THE RESULTTYPE PASSED IS NOT VALID!" 
				


			# feedback:
			print "\n\n++ = ++ = ++ = ++ = ++ = ++ = ++\n%s\nSTARTING CACHING FACET VALUES WITH PARAMS:"  % strftime("%Y-%m-%d %H:%M:%S")	
			print "facets: " + str([facet.uniquename for facet in all_facets])
			print "resulttypes:	 "	+ str([resulttype['uniquename'] for resulttype in all_resulttypes])
			print "enforce:	 "	+ str(options['enforce'])
			print "fmcache:	 "	+ str(options['fmcache'])
			print "reset:  "  + str(options['reset'])
			print "emptyunused:  "  + str(options['emptyunused'])
			print "++ = ++ = ++ = ++ = ++ = ++ = ++ = ++\n"




			#  now do the actions: 


			cacheDB = DbCache(FM_INSTANCE)



			# 1) cache the result types count  (later we'll have to make this an option for the command...)
			if True:
				cacheDB.cacheResultTypes()
					
			# 2) cache all the values
			if options['onlyrescounts'] == 'no':  # option for caching only the tot resultTypes counts
				for facet in all_facets:
					for r in all_resulttypes:
						if not facet.get_behaviour(r['uniquename']): 
							print "\n WARNING ==> There is no behaviour defined for	 ...  [facet=%s, resType=%s]" % (str(facet.uniquename), r['uniquename'])
						else:					
							print "\n...started caching at [%s] ...... [facet=%s, resType=%s]"	 %	(strftime("%Y-%m-%d %H:%M:%S"), str(facet.uniquename), r['uniquename'])
							v = cacheDB._cacheOneFacet(facet, resulttype=r, ENFORCE=ENFORCE) 
							if v:
								print "\n[%s]\nzzzzzzzzzzzzzzzzzz sleeping 1 second zzzzzzzzzzzzzzzzzzzzzzzz\n\n"	% strftime("%Y-%m-%d %H:%M:%S")
								time.sleep(1)
					

						
				print '\nSuccessfully cached facets [%s]' % (str([facet.uniquename for facet in all_facets]))
				#  let's clean the cache for unused elements...
				print "\nNow emptying unused elements....."
				print "....DONE: tot emptied elements= %d"	% cacheDB._emptyUnusedElements()


