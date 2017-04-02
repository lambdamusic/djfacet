
def determine_ordering(result_type, ordering):
	""" Helper function that maps a user-selected 'ordering_string' (eg <option1>, <option2> etc.) to the fields names (or list of) 
	to be passed to the run_query (in FM) for ordering the result list	"""
	
	reverse_flag = False
	
	#  example orderings.. fill out with your own data
	ORDERINGS = { 'restype1' :	   { 'option1' : ['field1__name'], 
									'option2' : ['field2__name'],
									'option3' : ['field3__id'],									
										} ,

				'restype2' :  { 'option1' : ['field1__name'], 
								'option2' : ['field2__name'],
								'option3' : ['field3__id'],									
													},
				#	etc.....
				}

	DEFAULT_ORDERINGS = {	
							'restype1' : 'option1', 
							'restype2' : 'option2', 
							# etc...
							}

	if ordering.startswith('-'):
		ordering = ordering.replace("-", "")
		reverse_flag = True

	try:
		# this fails in some cases (eg when switching res type) so we use the exception!
		chosen_ordering = ORDERINGS[result_type][ordering]
	except:
		ordering = DEFAULT_ORDERINGS[result_type]	# by default
		chosen_ordering = ORDERINGS[result_type][ordering]

	if reverse_flag:
		return ['-' + x for x in chosen_ordering ]
	else:
		return chosen_ordering
