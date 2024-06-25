from django.contrib import admin

from .models import *

admin.site.register(Schedule)
admin.site.register(TripSchedulerMapper)
admin.site.register(DutyList)
admin.site.register(DutyListMapper)