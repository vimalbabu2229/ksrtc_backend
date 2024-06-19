from django.contrib import admin
from .models import User, Depot, Employee

# Register your models here.
admin.site.register(User)
admin.site.register(Depot)
admin.site.register(Employee)