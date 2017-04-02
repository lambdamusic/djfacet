# templatetags used in djfacet 

from django import template
from djfacet.fb_utils.utils import *

register = template.Library()



@register.filter
def extract_father(fvalue):
	""" splits a list into two parts"""
	if fvalue.father:
		father = fvalue.facet.get_facetvalue_from_id(fvalue.father)
		return "%s" % father.displayname
	else:
		return ""


@register.filter
def split_list(somelist):
	""" splits a list into two parts"""
	return split_list_into_two(somelist)



@register.filter
def fvlist_formatter(facetvalues, case_sensitive=False):
	""" Takes a list of facetvalues and returns a dict usable in singlefacet.html. 
		{{ with somelist|fvlist_formatter1 as xx }}, or {{ with somelist|fvlist_formatter1:"True" as xx }}
	
		The nested list is organized by initials and it also splits the facetvalues list into two groups, as required by the template (and maintaining ordering). Eg.

		First we construct a dict
			{ "A" : [(fv1, fv2, fv3 etc), (fv4, fv5, fv6 etc)], "B" : [(fv1, fv2, fv3 etc), (fv4, fv5, fv6 etc)], etc.. }
		We transform it into an ordered tuple containing nested lists:
			[ ("A" : [(fv1, fv2, fv3 etc), (fv4, fv5, fv6 etc)]), ("B" : [(fv1, fv2, fv3 etc), (fv4, fv5, fv6 etc)]), etc.. }

	
	PS: This is a wrapper for the two functions below (one for strings and one for numbers)

	"""

	if facetvalues[0] and is_number(facetvalues[0].displayname):
		return numbers_formatter(facetvalues, case_sensitive)
	else:
		return strings_formatter(facetvalues, case_sensitive)


def numbers_formatter(facetvalues, case_sensitive=False):
	""" 
	2012-08-08:
	Facetvalues-list formatter: added support for numbers
	
	If the interval is not provided, and interval is created by taking the min and max values and 
	dividing that space in 20 parts. The interval is the 1/20th of that space.
	
	"""
	mydict = {}
	# get the appearance options for numbers from the specs, if available
	interval = facetvalues[0].number_opts.get('range_interval', None)
	format = facetvalues[0].number_opts.get('format', 'default')
	show_singlefacet_header = facetvalues[0].show_singlefacet_header
		
	def match_range(ranges, num):
		"""
		Matches a num against a range-list as outputted by  buildranges() eg
		[('990-1020', (990, 1020)), ('1020-1050', (1020, 1050))] 		
		"""
		for rang in ranges:
			nums_tuple = rang[1]
			if num >= nums_tuple[0] and num < nums_tuple[1]:
				return rang[0]
		return None
	
	if show_singlefacet_header:
		all_numbers = [x.displayname for x in facetvalues]
		# if interval isn't specified, create a default one based on total range of numbers 
		if not interval:
			interval = (max(all_numbers) - min(all_numbers)) / 20
		maxN = findmax(interval, max(all_numbers))	
		minN = findmin(interval, min(all_numbers))	

		# create ranges set
		if format == "commas":  #formats big numbers with commas
			ranges_opts = buildranges_withFormat(minN, maxN, interval)
		elif format == "default":
			ranges_opts = buildranges(minN, maxN, interval)
		else:  # fails silenty 
			ranges_opts = buildranges(minN, maxN, interval)
	
		for val in facetvalues:
			range_key = match_range(ranges_opts, val.displayname)
			if range_key:
				if range_key not in mydict.keys():
					mydict[range_key] = [val]
				else:
					mydict[range_key] += [val]					
	else:
		mydict["All values"] = facetvalues
					
					
	# now split the lists, to accommodate the 2-columns display
	for el in mydict.keys():
		mydict[el] = split_list_into_two(mydict[el])
	# sort
	keys = mydict.keys()
	if show_singlefacet_header:
		keys.sort(key=lambda x: num(x.split("-")[0].replace(",", "")))
	else:
		pass

	return [(key, mydict[key]) for key in keys]
	
	
	


def strings_formatter(facetvalues, case_sensitive=False):
	""" 
	Format strings 
	"""
	mydict = {}
	show_singlefacet_header = facetvalues[0].show_singlefacet_header

	if show_singlefacet_header:
		# if in the single_facet template we want the alpha index at the top
		for val in facetvalues:
			if case_sensitive:
				if val.displayname[0] not in mydict.keys():
					mydict[val.displayname[0]] = [val]
				else:
					mydict[val.displayname[0]] += [val]
			else:
				if val.displayname[0].upper() not in mydict.keys():
					mydict[val.displayname[0].upper()]= [val]
				else:
					mydict[val.displayname[0].upper()] += [val]
	else:
		mydict["All values"] = facetvalues

	# now split the lists, to accommodate the 2-columns display
	for el in mydict.keys():
		mydict[el] = split_list_into_two(mydict[el])
	# sort
	keys = mydict.keys()
	keys.sort()
	return [(key, mydict[key]) for key in keys]
	# return mydict

	












# 2012-05-10: UNUSED ?
# ===>	if we keep this approach, we might just remove the little formatting code in ..._inner.html 
@register.inclusion_tag('djfacet/snippet_mpttfacet_inner.html')
def render_tree(facetvalues, facet, facetgroup):
	
	if False:  # testing 
		stuff = []
		for x in facetvalues:
			stuff.append(facet.recursive_tree_forfacetvalue(x))

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
	return { 
			'stringa' : stringa,
			'facet_id' : facet.id, 
			
			# 'stuff' : stuff,		
			# 'facet' : facet,			
			# 'facetvalues': facetvalues, 
			# 'facetgroup' : facetgroup
			}



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
	


