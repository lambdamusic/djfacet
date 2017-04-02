from time import strftime
from djfacet.constants import *
from django.http import QueryDict
import locale
locale.setlocale(locale.LC_ALL, '')	 # UK

try:
	from settings import DEBUG
except:
	DEBUG = False



##################
#
#  FACETED MANAGER AND VIEWS UTILS
#
##################




def get_defaultResType():
	""" gets the specified default resulttype - or the first one in case we can't find it """
	for x in DJF_SPECS.result_types:
		if x.get('isdefault'):
			return x
	return DJF_SPECS.result_types[0]



def validate_ResType(restype_candidate_string):
	""" from a string (normally passed through the url) this function checks
		that it matches one of the result type. If it fails it returns the default one.
	"""
	RESULT_TYPES = DJF_SPECS.result_types 
	if not restype_candidate_string or restype_candidate_string not in [x['uniquename'] for x in RESULT_TYPES]:
		DEFAULT_RESULTTYPE = get_defaultResType()
		return DEFAULT_RESULTTYPE['uniquename']
	else:
		return restype_candidate_string			


def getHTMLColor(index):
	try:
		return SOFT_HTML_COLORS[index]
	except:
		return SOFT_HTML_COLORS[1]




def create_queryUrlStub(query_filtersUrl=None):
	""" from the active filters, pre-compose the url so that it can be used in the template more easily where is needed 
		Returns a string like this : "&filter=2&filter=3&filter=4&filter1=2&filter1=3&filter1=4"
	"""
	stringa = "filter=0"  # initialize
	newurl_stub = ""
	if query_filtersUrl:
		q=QueryDict(stringa).copy()
		q.setlist('filter', query_filtersUrl)
		newurl_stub =q.urlencode()	# eg: 'filter=2&filter=3&filter=4&filter1=2&filter1=3&filter1=4'
		newurl_stub = "&"+ newurl_stub
		# print newurl_stub
	return newurl_stub








##################
#
#  MPTT/TREE MANAGEMENT UTILS
#
##################


# once we obtained the tree_dict with the IDs, here we check again that only the values with updated howmany are passed
# OPTIMIZE? ? ? change the method in facet.py ? 

def tree_visualizer(root, tree_dict, res, facet, facetgroup, facetvalues):
	for x in tree_dict[root]:
		facetvalue = [v for v in facetvalues if v.id == x]
		if facetvalue:
			res += """<li style="font-size:12px;"><a id="%s_%d" class="%s" >%s (%d)</a>""" % (facetgroup.uniquename, 
				facetvalue[0].id, facet.name, facetvalue[0].displayname,  facetvalue[0].howmany)
		else:
			facetvalue = facet.get_facetvalue_from_id(x)
			res += """<li>%s""" % facetvalue.displayname  #<span style="color: #2C528B;">%s</span>
		if tree_dict.get(x):
			# djfacetlog("noise")
			res += "<ul>" + tree_visualizer(x, tree_dict, '', facet, facetgroup, facetvalues) + "</ul>"
		res += "</li>"
	return res
	
	
	
	
def render_tree_string(facetvalues, facet, facetgroup):
	if True:
		stringa = ""
		#  the dict cointains the tree structure with IDs only
		djfacetlog("\n STARTING LOADING THE TREE............... \n")
		mydict = facet.recursive_tree_forfacetvalue_list(facetvalues)
		djfacetlog("\n DONE LOADING THE TREE \n")
		# stringa ideally should be built inside the template, using a recursive model.. TODO
		djfacetlog("\n STARTING VISUALIZING THE TREE............... \n")
		stringa = tree_visualizer(0, mydict, "", facet, facetgroup, facetvalues)
		djfacetlog("\n DONE VISUALIZING THE TREE \n")			
	return stringa 
	


def num(s):
	"""
	Returns a number from a string
	"""
	try:
		return int(s)
	except:
		return float(s) 
	
	


def findmin(rangen, n):
	""" Given an interval-range-value (eg 30) and a number (eg 80) return the minimum range value
		available for that number (=60). Used to decide where to START a range sequence
	 """
	e = 0
	while e < n:
		e += rangen
		# returns the one before
	return e - rangen

def findmax(rangen, n):
	""" Given an interval-range-value (eg 30) and a number (eg 80) return the maximum range value
		available for that number (=60). Used to decide where to END a range sequence
	 """
	e = 0
	while e < n:
		e += rangen
		# returns the one after
	return e


def format_float_nice(f):
	"""
	abstraction for nice formatting of floats:
	http://stackoverflow.com/questions/2440692/formatting-floats-in-python-without-superfluous-zeros
	"""
	return (locale.format("%f", f, grouping=True)).rstrip('0').rstrip('.')


def buildranges_withFormat(amin, amax, rangeval):
	"""Retunrs a list of tuples, with the string-range first and then
	 the numbers in a tuple: 
	[('990-1020', (990, 1020)), ('1020-1050', (1020, 1050))]  

	This is an enhanced version of the code below. 
	It includes numbers formatting (good for big numbers) and support for int/float too
	"""
	r = []
	allvalues = range(amin, amax, rangeval)
	for index, item in enumerate(allvalues):
		if (index + 1) < len(allvalues):
			if type(rangeval) == type(1.5):	 #float: will allow 5 decimal digit (todo: less?)
				a = "%s-%s" % (format_float_nice(item), format_float_nice(allvalues[index + 1]))				
			elif type(rangeval) == type(1) or type(rangeval) == type(1L):  # int or Long: will cut decimal values
				a = "%s-%s" % (locale.format("%d", item, grouping=True),  locale.format("%d", allvalues[index + 1], grouping=True))
			else:
				djfacetlog("<buildranges_withFormat>: Number Type not recognized [%s]" % str(type(rangeval)))
				a = "%s-%s" % (locale.format("%d", item, grouping=True),  locale.format("%d", allvalues[index + 1], grouping=True))

			r.append((a, (item, allvalues[index + 1])))
	return r




def buildranges(amin, amax, rangeval):
	"""Retunrs a list of tuples, with the string-range first and then
	 the numbers in a tuple: 
	[('990-1020', (990, 1020)), ('1020-1050', (1020, 1050))]  
	"""
	r = []
	allvalues = range(amin, amax, rangeval)
	for index, item in enumerate(allvalues):
		if (index + 1) < len(allvalues):
			a = "%d-%d" % (item, allvalues[index + 1])
			r.append((a, (item, allvalues[index + 1])))
	return r


	



##################
# GENERIC UTILS
##################





def clearExpiredSessions():
	"""
	Util that empties the expired Django sessions from the DB table.
	2012-09-04: added if statement based on tot num of rows in table
	"""
	# djfacetlog("---UTILS/ClearExpiredSessions(): starting")
	from django.contrib.sessions.models import Session
	tot = Session.objects.count()
	if tot > 50:
		djfacetlog("---UTILS/ClearExpiredSessions(): cleaning table with expired sessions...")
		import datetime
		Session.objects.filter(expire_date__lte = datetime.datetime.now()).delete()
		djfacetlog("...... clearExpiredSessions() applied succesfully :-) (threshold=50)")
	# else:
	# 	djfacetlog("...... not run as session table has only %d rows (threshold=50)" % tot)






def djfacetlog(stringa, override = False):
	""" simple utility function that prints a debug string is DJF_SHOWLOGS is True
		If DEBUG= True it assumes we're using runserver, otherwise it tries to write it to a file
		and fails silently 
	"""
	if DJF_SHOWLOGS or override:
		if stringa == 'noise':
			stringa = "\n%s\n" % ("*&*^" * 100)
		if DEBUG:
			try:
				print ">>[%s]djfacetDebug>>: %s"	% (strftime("%Y-%m-%d %H:%M:%S"), stringa)
			except:
				pass
		else:
			file = "/tmp/djfacet_log.txt"
			try:
				handle = open(file,"a")
				now = "--%s--\n"	% strftime("%Y-%m-%d %H:%M:%S")
				handle.write( now + stringa +"\n")
				handle.close()
			except:
				pass




def best_encoding(x_to_encode):
	out = None
	if type(x_to_encode) == type(1) or type(x_to_encode) == type(1L):  # type int or long
		out = str(x_to_encode)
	else:
		try:
			out = x_to_encode.encode('utf-8')		
		except:
			try:
				out = x_to_encode.encode('iso-8859-1')
			except:
				raise Exception("** could not encode **")
				# out = "** could not encode **"
	return out


def blank_or_string(s):
	"""If it's empty, output the string blank"""
	if not s.strip():
		return 'blank'
	return s


def preview_string(s, length):
	"""If we have a value, returns the first [length] chars of the string.."""
	if s:
		if	len(s) < length:
			result = unicode(s) 
		else:
			result = unicode(s)[0:length] + "..."
		return result

def isint(s):
	"""checks if a string is a number"""
	try:
		return int(s)
	except ValueError:
		return False




def split_list_into_two(somelist):
	x = len(somelist)
	z = x/2
	return [somelist[:(x -z)], somelist[(x -z):]]



def group_list_items_by_two(lista, listaexit= None):
	lista_x = []
	listaexit = listaexit or []
	if lista:
		lista_x.extend(lista)
		lista_x.reverse()		
		first_el = lista_x.pop()
		if len(lista_x) == 0:
			second_el = None 
		else:
			second_el = lista_x.pop()
		listaexit.append([first_el, second_el]) 
		if lista[2:]:
			group_list_items_by_two(lista[2:], listaexit)
		#print(listaexit)
		return listaexit



filler = ["value_%s" % (i) for i in range(10)]


# given a center, returns a list of the neighbouring numbers according to the paramenters passed
def paginator_helper(center, max, howmany=5, interval=1, min=1, ):
	if center - howmany > min:
		min = center - howmany
	if center + howmany < max:
		max = center + howmany
	return range(min, (max + 1), interval)





#  helper for django models : NEVER USED
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





def list_difference(list1, list2):
	""" returns the difference between two lists """
	return [x for x in list1+list2 if x not in list1 or x not in list2]


def is_number(s):
	try:
		float(s) # for int, long and float
		return True
	except ValueError:
		return False




