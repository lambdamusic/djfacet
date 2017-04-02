# FILE THAT CAN BE LOADED INTO THE SHELL USING AN IMPORT STATEMENT
# USED ONLY IN DEVELOPMENT, FOR TESTING THE FM OBJECT USE 'DJFACET_SHELL' COMMAND



from djfacet.constants import *
from djfacet.views import *


#  init vars
loaded_facet_groups = []
facets_for_template = []

# load facet specs 
# 1: create groups from SPECS.facet_groups	
for x in reversed(sorted(DJF_SPECS.facet_groups, key=lambda (k): k['position'])):
	if x['default']:
		loaded_facet_groups.append(FacetsGroup(x['uniquename'], x['label'], x['position'])) 
# 2: load facets into groups using SPECS.facetslist
for g in loaded_facet_groups:
	g.buildfacets_fromspecs(DJF_SPECS.facetslist)
# 3: load result types
result_types = DJF_SPECS.result_types 

# initialize the faceted manager
f = FacetedManager(loaded_facet_groups, result_types)

# prepare data for visualization
for g in loaded_facet_groups:
	facets_for_template.append((g, [(facet, split_list_into_two(facet.get_facetvalues_sample(maxnumber=0))) for facet in g.facets]))	
	

#  feedback:
print '+++ Loaded facet groups:'
for x in loaded_facet_groups: print x.uniquename, x.position

print '+++ loaded result types:'
for x in result_types: print x['uniquename'], " : ", x['infospace']


if True:
	f.init_resulttypes_activeIDs()


logs = """ 
COMMANDS LOADED:::
===================
for x in reversed(sorted(SPECS.facet_groups, key=lambda (k): k['position'])):
	if x['default']:
		loaded_facet_groups.append(FacetsGroup(x['uniquename'], x['label'], x['position']))	
for g in loaded_facet_groups:
	g.buildfacets_fromspecs(SPECS.facetslist)
# 3: load result types
result_types = DJF_SPECS.result_types 

# initialize the faceted manager
f = FacetedManager(loaded_facet_groups, result_types)

# prepare data for visualization
for g in loaded_facet_groups:
	facets_for_template.append((g, [(facet, split_list_into_two(facet.get_facetvalues_sample(maxnumber=0))) for facet in g.facets]))

#  feedback:
print '+++ Loaded facet groups:'
for x in loaded_facet_groups: print x.name, x.position

print '+++ loaded result types:'
for x in result_types: print x['uniquename'], " : ", x['infospace']

f.init_resulttypes_activeIDs()

# to TEST the DBcache:
>>> genderfacet = f.get_facet_from_name('gender')
>>> genderval = genderfacet.get_facetvalue_from_displayname('M')
>>> queryargs = [[None, genderfacet, genderval]]
>>> cacheDB = DbCache(f, queryargs, None)
>>> cacheDB.getCachedFacetValues('source', genderfacet)
>>> cacheDB.getCachedFacetValue_fromValue(genderfacet, 'source', 'M')
>>> cacheDB.getCachedFacetValueCount_fromValue(genderfacet, 'source', 'M')


===================
"""

print logs

genderfacet = f.get_facet_from_name('gender')
genderval = genderfacet.get_facetvalue_from_displayname('M')
queryargs = [[None, genderfacet, genderval]]
cacheDB = DbCache(f, queryargs, None)