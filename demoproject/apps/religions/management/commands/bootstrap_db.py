from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from django.conf import settings
from django.db import connection, models
from time import strftime
import time, csv

from religions.models import *
from settings import printdebug


##################
#  2011-03-22
#	
#  This script bootstraps the contents of the DB from the comma separated file
# 
#
##################



#  helper for django models 
def get_or_new(model, somename):
	"""helper method"""
	try:
		# if there's an object with same name, we keep that one!
		obj = model.objects.get(name= somename)
		print "++++++++++++++++++++++++++ found existing obj:	%s"	 % (obj)
	except:
		obj = model(name = somename)
		obj.save()
		print "======= created new obj:	  %s"  % (obj)
	return obj





# EG:
# bash-3.2$ python manage.py bootstrap_db

class Command(BaseCommand):
	args = '<no args >'
	help = 'bootstrap the db'


	def handle(self, *args, **options): 
		"""
		args - args 
		options - configurable command line options
		"""


		# feedback:
		print "\n\n++ = ++ = ++ = ++ = ++ = ++ = ++ = ++\n%s\nSTARTING CREATING DB:"  % strftime("%Y-%m-%d %H:%M:%S")	
		print "++ = ++ = ++ = ++ = ++ = ++ = ++ = ++\n"


		#  now do the actions: 
		if True:			
			myFile = open("religion_data.csv", 'rU')
			reader = csv.reader(myFile)	  # ==> outputs lists

# EG  of data: 

# ['IDB Region', 'WorldFactbook region', 'Country', 'pop2000', 'pop2008', '', 'Country', 'Christian', 'Muslim', 'Hindu', 'Buddhist', 'Other/UnSpecified', 'Jewish', 'None', '', 'Main Religion', 'subgroups or other religions.', '', '', '', '', '', '', '', '', '', '', '']
# ['ASIA (EXCLUDING NEAR EAST)		   ', 
	# 'Asia', 
	# 'Afghanistan						  ', 
	# '23898198', 
	# '32738376', 
	# '',	 [5]
	# 'Afghanistan', 
	# '', 
	# '99.0%', 
	# '', 
	# '',	[10]
	# '1.0%', 
	# '', 
	# '', 
	# '', 
	# 'Muslim',	  [15]
	# 'Sunni Muslim 80%', ' Shia Muslim 19%', ' other 1%', '', '', '', '', '', '', '', '', '']
			
		
			for row in reader:
				if row:
					# 1. extract the regions
					print "*" * 50, "\n", row, "\n", "*" * 50
					
					regionname = row[1].strip()
					regionidbname = row[0].strip()
					if Region.objects.filter(name= regionname, idbname = regionidbname):
						region = Region.objects.get(name= regionname, idbname = regionidbname)
						print "++++++++++++++++++++++++++ found existing obj:	%s"	 % (region)
					else:
						region = Region(name= regionname, idbname = regionidbname)
						region.save()
					
					countryname = row[6].strip()
					if countryname:
						country = get_or_new(Country, countryname)
						if row[3].strip():
							country.pop2000 = float(row[3].strip())
						if row[4].strip():
							country.pop2008 = float(row[4].strip()) 
						country.inregion = region
						country.save()				
					
					# 2. extract the religions
					for number in range(16, 28):
						try:
							religionfield = row[number].strip()
						except:
							religionfield = None
							printdebug("Row number not accepted! --%s--" % number)
						if religionfield:
							religionname = " ".join([x for x in row[number].strip().split(" ") if not "%" in x])
							religionpercent = " ".join([x for x in row[number].strip().split(" ") if "%" in x])
							numberstring = religionpercent.replace("%", "")
							try:
								number = float(numberstring)
							except:
								number = None
								printdebug("Count'd extract number from --%s--" % numberstring)
						
							if religionname:
								religion = get_or_new(Religion, religionname)
								rr = ReligionInCountry(country=country, religion=religion, percentage=number)
								rr.save()
					
								
					
					print "\n"


			myFile.close()				


		printdebug("************\nCOMPLETED\n************")

