from religions.models import *



##################
#  
#  RESULT_TYPES and FACET_GROUPS
#
##################



facetslist = []




#	label = interface name / uniquename = internal name / infospace: a Model or a QuerySet instance
result_types	 = [{	'label' : 'Religions', 
						'uniquename' : 'religions', 
						'infospace' : Religion	,
						'isdefault' : True
						   },
						
					 {	'label' : 'Countries', 
						'uniquename' : 'country',  
						'infospace' : Country,
							},

					]
			 

facet_groups =		[{	'label':	'Place facets', 
						'position': 1,
						'uniquename' :	'countrygroup', 
						'default' : True  , 
						'bkcolor' : 'FFEEFF' } ,
						
					{	'label':	'Religion facets', 
						'position': 2,
						'uniquename' :	'religiongroup', 
						'default' : True   ,
						'bkcolor' : "EEFFFF"} ,
					]






##################
#  
#  FACETS
#
##################


facetslist +=	[ 


# @@@	
# 	PLACE FACETS
# @@@


			{	'active' : True, 
				'explanation': "Standard name of Geographical Regions", 
				'uniquename' : 'regionname',
				'model' : Region ,
				'appearance' : {'label' : 'Region name' , 
								'dbfield' : "name", 
								'displayfield' : "name", 
								'grouping'	: ['countrygroup'],
								'ordering' : 'name',
								} ,
				'behaviour' :  [{'resulttype' : 'religions',
								 'querypath' : 'country__inregion__name', 
								 'explanation' : "showing all...." },
								{'resulttype' : 'country',
								 'querypath' : 'inregion__name', 
								 'explanation' : "showing all...." },
								]
						 },
									


			{	'active' : True, 
				'explanation': "Alternative (IDB) Name for Geographical Regions",
				'uniquename' : 'regionidbname',
				'model' : Region ,
				'appearance' : {'label' : 'Region idbname' , 
								'dbfield' : "idbname", 
								'displayfield' : "idbname", 
								'grouping'	: ['countrygroup'],
								'ordering' : 'idbname',
								} ,
				'behaviour' :  [{'resulttype' : 'religions',
								 'querypath' : 'country__inregion__idbname', 
								 'inversepath' : None,
								 'explanation' : "showing all...." },
								{'resulttype' : 'country',
								 'querypath' : 'inregion__idbname', 
								 'inversepath' : None,
								 'explanation' : "showing all...." },
								]
						 },

			{	'active' : True, 
				'explanation': "Standard Country Names",
				'uniquename' : 'countryname',
				'model' : Country ,
				'appearance' : {'label' : 'Country name' , 
								'dbfield' : "name", 
								'displayfield' : "name", 
								'explanation': "no explanation yet", # TODO: add explanations to all of them!
								'grouping'	: ['countrygroup'],
								'ordering' : 'name',
								} ,
				'behaviour' :  [{'resulttype' : 'religions',
								 'querypath' : 'country__name', 
								 'inversepath' : None,
								 'explanation' : "showing all...." },
								
								# NOTE THAT THIS FACET WILL NOT WORK WITH COUNTRIES!
								# ...if it did.. it could look like this:
								
								# {'resulttype' : 'country',
								#  'querypath' : 'name', 
								#  'inversepath' : None,
								#  'explanation' : "showing all...." },
								]
						 },
	
	
			{	'active' : True, 
				'explanation': "Population in 2008",
				'uniquename' : 'pop2008',
				'model' : Country ,
				'appearance' : {'label' : 'Population (2008)' , 
								'dbfield' : "pop2008", 
								'displayfield' : "pop2008", 
								'grouping'	: ['countrygroup'],
								'ordering' : 'pop2008',
								'show_singlefacet_header' : True,
								'number_opts' : {'range_interval' : 10000000, 'format' : 'commas'},
								} ,
				'behaviour' :  [{'resulttype' : 'religions',
								 'querypath' : 'country__pop2008', 
								 'inversepath' : None,
								 'explanation' : "showing all...." },
								{'resulttype' : 'country',
								 'querypath' : 'pop2008', 
								 'inversepath' : None,
								 'explanation' : "showing all...." },
								]
						 },
	
	
	
# @@@	
# 	RELIGION FACETS
# @@@
						
				# THIS IS AN MPTT/HIERARCHICAL FACET		

				{	'mptt' : True,
					'explanation': "Hierarchical classification of religions", 
					'uniquename' : 'religionname',
					'model' : Religion ,
					'appearance' : {'label' : 'Religion name' , 
									'dbfield' : "name", 
									'displayfield' : "name", 
									'grouping'	: ['religiongroup'],
									'ordering' : 'name',
									} ,
					'behaviour' :  [{'resulttype' : 'religions',
									 'querypath' : 'name', 
									 'inversepath' : None,
									 'explanation' : "showing all...." },
									{'resulttype' : 'country',
									 'querypath' : 'religions__name', 
									 'inversepath' : None,
									 'explanation' : "showing all...." },
									]
							 },



				# NOW LET'S DEFINE A CUSTOM FACET (NOT WORKING YET SO It's DISABLED) :

				{	'active' : False,
					'explanation': "no explanation yet", 
					'uniquename' : 'myreligions',
					'model' : Religion ,
					'appearance' : {'label' : 'My Religions' , 
									'dbfield' : "name", 
									'displayfield' : "name", 
									'grouping'	: ['religiongroup'],
									'ordering' : 'name',
									'customvalues' :	{
										'religions I am interested in' : 
											{'id__in' : [172, 158, 48],},
										'religions I already know' : 
											{'id__in' : [54, 59],} 
											}
								   } ,
								
					'behaviour' :  [{'resulttype' : 'religions',
									 'querypath' : 'name', 
									 'inversepath' : None,
									 'explanation' : "showing all...." },
									{'resulttype' : 'country',
									 'querypath' : 'religions__name', 
									 'inversepath' : None,
									 'explanation' : "showing all...." },
									]
							 },		
		
		
						
						#	end of facet_list
								]



