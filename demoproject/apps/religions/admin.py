from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import *
from django.utils.translation import ugettext_lazy as _

from religions.models import *


admin.site.register(Country, Country.Admin)
admin.site.register(Region, Region.Admin)
admin.site.register(Religion, Religion.Admin)






