import re
from django import http, template
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy, ugettext as _ 

from settings import printdebug
import datetime
# from MYAPP.models import *


# #####
# CUSTOM VIEWS FOR THE ADMIN APPLICATION
#  if you want to order the table_groups in the app_index.html view, it's faster to 'trick' it using numbers at the 
# beginning of the headings
# #####


@staff_member_required
def MYAPP(request, url):
	url = url.rstrip('/') # Trim trailing slash, if it exists.
	admin.site.root_path = re.sub(re.escape(url) + '$', '', request.path)
	return app_index(request, url)


# This method is mostly copied from [PYTHON]\Lib\site-packages\django\contrib\admin\sites.py, app_index()
# It splits all the tables into groups, the name of the group they belong to is determined by the "table_group" variable in the models
# It uses the existing application templates ([PYTHON]\Lib\site-packages\django\contrib\admin\templates\admin\app_index.html)
# No need to extend that template
def app_index(request, app_label, extra_context=None):
	user = request.user
	has_module_perms = user.has_module_perms(app_label)
	app_list = {}
	app_dict = {}
	for model, model_admin in admin.site._registry.items():
		if app_label == model._meta.app_label:
			if has_module_perms:
				perms = {
					'add': user.has_perm("%s.%s" % (app_label, model._meta.get_add_permission())),
					'change': user.has_perm("%s.%s" % (app_label, model._meta.get_change_permission())),
					'delete': user.has_perm("%s.%s" % (app_label, model._meta.get_delete_permission())),
				}
				# GN - use the table group as an index for the app
				try:
					app_index = model.table_group
				except AttributeError:
					app_index = ''	
				# NEW michele: I added an extra property for ORDERING manually the model list
				try:
					app_order = model.table_order
				except AttributeError:
					app_order = 0
				# Check whether user has any perm for this module.
				# If so, add the module to the model_list.
				if True in perms.values():
					model_dict = {
						'name': capfirst(model._meta.verbose_name_plural),
						'admin_url': '%s/' % model.__name__.lower(),
						'perms': perms,
						'order': app_order,
						#'reference': model.reference_table,
					}
					if (app_index in app_list):
						app_list[app_index]['models'].append(model_dict),
					else:
						# First time around, now that we know there's
						# something to display, add in the necessary meta
						# information.
						app_list[app_index] = {
							'name': app_label.title(),
							'app_url': '',
							'has_module_perms': has_module_perms,
							'models': [model_dict],
							'order': app_order,
						}
						if (app_index != ''):
							app_list[app_index]['name'] += ' - ' + app_index
						#app_list.append(app_dict)	  
	#if not app_dict:
	#	 raise http.Http404('The requested admin page does not exist.')
	# Sort the models alphabetically within each app.
	app_list_final = []		
	for group_name, app in app_list.items():
		app['models'].sort(lambda x, y: cmp(x['name'], y['name'])) 
		# the list is sorted twice, so if there's no explicit order it falls back to the alphab. one
		app['models'].sort(lambda x, y: cmp(x['order'], y['order']))
		app_list_final.append(app)
	# 2011-10-25: sort the final list according to group names
	app_list_final.sort(key=lambda x: x['name'])
	context = {
		'title': _('%s administration') % capfirst(app_label),
		#'app_list': [app_dict],
		'app_list': app_list_final,
		'root_path': admin.site.root_path,
	}
	context.update(extra_context or {})
	return render_to_response(admin.site.app_index_template or 'admin/app_index.html', context,
		context_instance=template.RequestContext(request)
	)
	
	
	



from django.contrib.admin.models import LogEntry
	
# #####
#  VIEW of the recent contributors
# #####

@staff_member_required	
def contributions(request,):
	"The all-changes view for this application"
	my_data = []
	MAX_CHANGES = 1000
	logs = LogEntry.objects.all()[:MAX_CHANGES]
	# sometime the action_time method doesn't return a date, so let's make sure...
	temp =list(set([x.action_time.date() for x in logs if type(x.action_time) == type(datetime.datetime(2010, 10, 28, 15, 40, 57))]))
	
	for d in sorted(temp, reverse=True):
		my_data.append((d, LogEntry.objects.filter(action_time__year=d.year, action_time__month=d.month, action_time__day=d.day).order_by('user', 'action_time')))
		
	# printdebug(my_data)	
	
	return render_to_response( 
		"admin/contributions.html", 
		{'my_data' : my_data}, 
		RequestContext(request, {}), 
	)








