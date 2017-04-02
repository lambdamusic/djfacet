##################
#  THIS IS JUST AN EXAMPLE OF THE FACETSPECS.PY FILE THAT YOU NEED TO CREATE IN ORDER TO
#  CONFIGURE THE FACETED BROWSER
# 
#  THE SPECS FILE NEEDS TO BE LOCATED AT THE ROOT LEVEL OF YOUR PROJECT 
#  (I.E., WHERE YOU HAVE THE SETTINGS.PY FILE)
#  
#  MORE INFO AVAILABLE AT: http://www.michelepasin.org/support/djfacet/docs/configuration.html
##################



from myproject.mymodels import *



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

			{	'appearance' : {'label' : 'Region name' , 
								'uniquename' : 'regionname',
								'model' : Region , 
								'dbfield' : "name", 
								'displayfield' : "name", 
								'explanation': "no explanation yet", # TODO: add explanations to all of them!
								'grouping'	: ['countrygroup'],
								'ordering' : 'name',
								} ,
				'behaviour' :  [{'resulttype' : 'religions',
								 'querypath' : 'country__inregion__name', 
								 'inversepath' : None,
								 'explanation' : "showing all...." },
								{'resulttype' : 'country',
								 'querypath' : 'inregion__name', 
								 'inversepath' : None,
								 'explanation' : "showing all...." },
								]
						 },
									


			{	'appearance' : {'label' : 'Region idbname' , 
								'uniquename' : 'regionidbname',
								'model' : Region , 
								'dbfield' : "idbname", 
								'displayfield' : "idbname", 
								'explanation': "no explanation yet", # TODO: add explanations to all of them!
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

			{	'appearance' : {'label' : 'Country name' , 
								'uniquename' : 'countryname',
								'model' : Country , 
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
						
						
				# THIS IS AN MPTT/HIERARCHICAL FACET		

				{	'mptt' : True,
					'appearance' : {'label' : 'Religion name' , 
									'uniquename' : 'religionname',
									'model' : Religion , 
									'dbfield' : "name", 
									'displayfield' : "name", 
									'explanation': "no explanation yet", # TODO: add explanations to all of them!
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

		
						
						#	end of facet_list
								]





