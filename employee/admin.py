from django.contrib import admin
from .models import Employee, LeaveApplication

admin.site.register(Employee)

class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ('leave_type', 'employee', 'admin_read')
    ordering = ('-applied_on', )
admin.site.register(LeaveApplication, LeaveApplicationAdmin)
