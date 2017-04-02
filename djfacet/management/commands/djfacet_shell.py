# HACKED FILE FROM DJANGO_EXTENSIONS PACKAGE; FB SPECIFIC LOADERS HAVE BEEN ADDED....


import os
from django.core.management.base import NoArgsCommand
from optparse import make_option

# from _commandsimports import *
from djfacet.load_all import *



###################
#  Mon Jan 17 17:50:47 GMT 2011

# bash-3.2$ python manage.py djfacet_shell

#  This command loads a shell with added the following symbols:
#  	 'loaded_facet_groups' = ..		
#	 'result_types' = ..			
#	 'fm' = faceted manager instance
#
##################

	
	
class Command(NoArgsCommand):
	option_list = NoArgsCommand.option_list + (
		make_option('--plain', action='store_true', dest='plain',
			help='Tells Django to use plain Python, not IPython.'),
		make_option('--no-pythonrc', action='store_true', dest='no_pythonrc',
			help='Tells Django to use plain Python, not IPython.'),
	)
	help = "Like the 'shell' command but autoloads the models of all installed Django apps."

	requires_model_validation = True

	def handle_noargs(self, **options):
		# XXX: (Temporary) workaround for ticket #1796: force early loading of all
		# models from installed apps. (this is fixed by now, but leaving it here
		# for people using 0.96 or older trunk (pre [5919]) versions.
		from django.db.models.loading import get_models, get_apps
		loaded_models = get_models()

		use_plain = options.get('plain', False)
		use_pythonrc = not options.get('no_pythonrc', True)

		# Set up a dictionary to serve as the environment for the shell, so
		# that tab completion works on objects that are imported at runtime.
		# See ticket 5082.
		from django.conf import settings
		imported_objects = {'settings': settings}
		for app_mod in get_apps():
			app_models = get_models(app_mod)
			if not app_models:
				continue
			model_labels = ", ".join([model.__name__ for model in app_models])
			print self.style.SQL_COLTYPE("From '%s' autoload: %s" % (app_mod.__name__.split('.')[-2], model_labels))
			for model in app_models:
				try:
					imported_objects[model.__name__] = getattr(__import__(app_mod.__name__, {}, {}, model.__name__), model.__name__)
				except AttributeError, e:
					print self.style.ERROR_OUTPUT("Failed to import '%s' from '%s' reason: %s" % (model.__name__, app_mod.__name__.split('.')[-2], str(e)))
					continue

		# -----------------------------------------
		# 2010-11-03: Lines that build the facetedmanager object and make it available in the shell		
		
		try:
			#  MIND THAT IF <DJF_CACHE> IS SET TO TRUE AND THERE IS A CACHED VERSION OF THE FM, THAT'S WHAT'S BEEN USED!
			#  IF YOU PASS FORCE_CREATION=True then the FM IS RECONSTRUCTED
			FMGLOBAL = access_fmglobal()
			imported_objects['fm'] = FMGLOBAL

			#  feedback:
			print '+++ Loaded Facet Groups (<loaded_facet_groups> symbol):'
			for x in FMGLOBAL.facetsGroups: print x.uniquename, x.position

			print '+++ Loaded Result Types (<result_types> symbol):'
			for x in FMGLOBAL.result_types: print x['uniquename'], " : ", x['infospace']

			print '+++ Loaded Facets:'
			print str([x.uniquename for x in FMGLOBAL.get_all_facets()])
			
			print '\n+++ The Faceted Manager instance is available through the <fm> symbol\n'

			if True:
				FMGLOBAL.init_resulttypes_activeIDs()
			
			imported_objects['loaded_facet_groups'] = FMGLOBAL.facetsGroups
			imported_objects['result_types'] = FMGLOBAL.result_types			
			
		except:
			print "ERROR: could not load the faceted manager! "
			pass
			
		# -----------------------------------------
			
		try:
			if use_plain:
				# Don't bother loading IPython, because the user wants plain Python.
				raise ImportError
			import IPython
			# Explicitly pass an empty list as arguments, because otherwise IPython
			# would use sys.argv from this script.					
			shell = IPython.Shell.IPShell(argv=[], user_ns=imported_objects)
			shell.mainloop()
		except ImportError:
			# Using normal Python shell
			import code
			try: # Try activating rlcompleter, because it's handy.
				import readline
			except ImportError:
				pass
			else:
				# We don't have to wrap the following import in a 'try', because
				# we already know 'readline' was imported successfully.
				import rlcompleter
				readline.set_completer(rlcompleter.Completer(imported_objects).complete)
				readline.parse_and_bind("tab:complete")

			# We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
			# conventions and get $PYTHONSTARTUP first then import user.
			if use_pythonrc:
				pythonrc = os.environ.get("PYTHONSTARTUP") 
				if pythonrc and os.path.isfile(pythonrc): 
					try: 
						execfile(pythonrc) 
					except NameError: 
						pass
				# This will import .pythonrc.py as a side-effect
				import user
			code.interact(local=imported_objects)
			
			
			

		

		
