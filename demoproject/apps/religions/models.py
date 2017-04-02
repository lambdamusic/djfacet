
##################
#  Test models created by michele pasin, on
#  Tue Mar 22 11:00:01 GMT 2011
#  Data retrieved from http://gsociology.icaap.org [religions.xls] 
#  This data set shows the percent of the world population that is Christian, Muslim, Buddhist, Hindu, Jewish and None.
#  The majority of data are from the CIA World Factbook (2009)
##################



from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.conf import settings as django_settings

from utils.adminextra.autocomplete_tree_admin import AutocompleteTreeEditor
from utils.myutils import * 

import mptt




class Region(models.Model):
	"""(Region description)"""
	name = models.CharField(null=True, blank=True, verbose_name="name", max_length=765)
	idbname = models.CharField(null=True, blank=True, verbose_name="international db name", max_length=765)
	
	class Admin(admin.ModelAdmin):
		list_display = ('id', 'name', 'idbname')
		search_fields = ('name',)
		list_filter = ('name', )
	class Meta:
		verbose_name_plural="Region"
	def __unicode__(self):
		if self.name:
			return "%s %s" % ("Region:", self.name)
		else:
			return "%s %s" % ("Region ID:", self.id)
		



class ReligionInCountry(models.Model):
	#factoidpersonkey = models.IntegerField()
	country = models.ForeignKey('Country')
	religion = models.ForeignKey('Religion')
	percentage = models.FloatField(blank=True, null=True)

	def __unicode__(self):
		return "%s %s" % ("id:", self.id)

class ReligionInCountryInline(admin.TabularInline): # admin.TabularInline	 InlineAutocompleteAdmin
	model = ReligionInCountry
	verbose_name = 'Religion in Country'
	verbose_name_plural = 'Religion in Country'
	extra = 3




class Country(models.Model):
	"""(Country description)"""
	
	name = models.CharField(null=True, blank=True, verbose_name="name", max_length=765)
	pop2000 = models.FloatField(blank=True, null=True)
	pop2008 = models.FloatField(blank=True, null=True)
	inregion = models.ForeignKey('Region', null=True, blank=True, verbose_name="in region")
	religions = models.ManyToManyField('Religion', through='ReligionInCountry', verbose_name="has religions (with percentage)",)

		
	class Admin(admin.ModelAdmin):
		list_display = ('id', 'name', 'pop2000', 'pop2008', 'inregion')
		search_fields = ('name',)
		list_filter = ('name', )
		inlines = (ReligionInCountryInline, )
	class Meta:
		verbose_name_plural="Countries"
	def __unicode__(self):
		if self.name:
			return "%s %s" % ("Country:", self.name)
		else:
			return "%s %s" % ("Country ID:", self.id)




class Religion(models.Model):
	"""(Religion description)"""
	name = models.CharField(null=True, blank=True, verbose_name="name", max_length=765)
	parent = models.ForeignKey('Religion', null=True, blank=True, verbose_name="parent religion", related_name="sub_religion",)
		
	class Admin(AutocompleteTreeEditor):
		list_display = ('id', 'name', 'parent')
		search_fields = ('name',)
		list_filter = ('name', )
		related_search_fields = {	'parent': ('name',),   }
		actions = ['merge_religions']

		def merge_religions(self, request, queryset):
			message_bit = "Nothing"
			to_keep = list(queryset.order_by('id'))[0]
			to_merge = list(queryset.order_by('id'))[1:]
			print "Keep: ", to_keep, "\nMerge: ", to_merge
			# for obj in queryset:
			# 	to_merge.append(obj)
			if len(to_merge) > 0:
				for religion in to_merge:
					for rel in ReligionInCountry.objects.filter(religion=religion):
						rel.religion = to_keep
						rel.save()
					religion.delete()
			# 	pass
			
		merge_religions.short_description = "Merge selected Religions (the one with higher ID is kept)"
	
		def save_model(self, request, obj, form, change):
			"""adds the user information when the rec is saved"""
			if getattr(obj, 'created_by', None) is None:
				  obj.created_by = request.user
			obj.updated_by = request.user
			obj.save()
				
		def _actions_column(self, page):
			actions = super(Religion.Admin, self)._actions_column(page)
			actions.insert(0, u'<a href="add/?parent=%s" title="%s"><img src="%simg/admin/icon_addlink.gif" alt="%s"></a>' % (
				page.pk, _('Add child page'), django_settings.ADMIN_MEDIA_PREFIX , _('Add child page')))
			return actions
		

	def __nameandparent__(self):
		exit = ""
		if self.parent:
			return "%s (%s)" % (blank_or_string(self.name), blank_or_string(self.parent.name))
		else:
			return blank_or_string(self.name)

	def show_ancestors_tree(self):
		exit = ", ".join([blank_or_string(el.name) for el in self.get_ancestors().reverse()])
		if exit:
			exit = "%s (%s)" % (blank_or_string(self.name), exit)
		else:
			exit = blank_or_string(self.name)
		return exit
				
	class Meta:
		verbose_name_plural="Religion"
		ordering = ['tree_id', 'lft', 'name', ]			
			
	def __unicode__(self):
		return self.show_ancestors_tree()
	


mptt.register( Religion,)






