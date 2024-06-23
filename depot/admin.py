from django.contrib import admin
from .models import Depot, Vehicle, Trip

admin.site.register(Depot)
admin.site.register(Vehicle)
admin.site.register(Trip)