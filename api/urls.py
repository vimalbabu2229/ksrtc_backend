from django.urls import path, include
from rest_framework import routers
from accounts.views import AuthViewSet
from depot.views import DepotViewSet, DepotEmployeeViewSet, DepotVehicleViewSet, DepotTripsViewSet, DepotLeaveApplicationsView
from employee.views import EmployeeProfileView, LeaveApplicationView
from scheduler.views import DepotScheduleViewSet, EmployeeScheduleViewSet

router = routers.DefaultRouter()

# ________________________AUTHENTICATION ROUTER________________________

router.register(r'auth', AuthViewSet, basename='auth')
# End points :
#   POST    /api/auth/login/ 
#   POST    /api/auth/logout/
#   PATCH   /api/auth/reset_password/
#   PATCH   /api/auth/<employee_id>/remove/

# ___________________________ DEPOT ROUTERS _____________________________

router.register(r'depot', DepotViewSet, basename='depot')
# End points :
#   POST    /api/depot/
#   GET     /api/depot/

router.register(r'depot/employee', DepotEmployeeViewSet, basename='depot_employee')
# End points :
#   POST    /api/depot/employee/
#   GET     /api/depot/employee/
#   GET     /api/depot/employee/previous_employees/
#   GET     /api/depot/employee/<employee_id>/
#   PATCH   /api/depot/employee/<employee_id>/
#   DEL     /api/depot/employee/<employee_id>/

router.register(r'depot/vehicles', DepotVehicleViewSet, basename='depot_vehicles')
# End points :
#   POST    /api/depot/vehicles/
#   GET     /api/depot/vehicles/
#   GET     /api/depot/vehicles/previous_vehicles/
#   GET     /api/depot/vehicles/<vehicle_id>
#   PATCH   /api/depot/vehicles/<vehicle_id>
#   DEL     /api/depot/vehicles/<vehicle_id>

router.register(r'depot/trips', DepotTripsViewSet, basename='depot_trips')
# End points :
# 
router.register(r'depot/leave_applications', DepotLeaveApplicationsView, basename='depot_leave_applications')
# End points :
# 

# ___________________________ EMPLOYEE ROUTERS _____________________________
router.register(r'employee/profile', EmployeeProfileView, basename='employee_profile')
# End points:
#   GET     /api/employee/profile/

router.register(r'employee/leave_applications', LeaveApplicationView, basename='employee_leave_applications')
# End points:
#

# ___________________________ SCHEDULER ROUTERS _____________________________
router.register(r'scheduler/depot', DepotScheduleViewSet, basename='depot_scheduler')
# End points:
#   
router.register(r'scheduler/employee', EmployeeScheduleViewSet, basename='employee_scheduler')
# End points:
# 

# register the duty list url separately in order to accept a pk also to get a particular duty list 
custom_urls = [
    path('scheduler/depot/duty_list/', DepotScheduleViewSet.as_view({'get':'duty_list'}), name='depot_duty_list'), 
    # GET /api/scheduler/depot/duty_list/ ==> gives the current active duty list
    path('scheduler/depot/duty_list/<int:pk>/', DepotScheduleViewSet.as_view({'get':'duty_list'}), name='depot_duty_list_with_pk'), 
    # GET /api/scheduler/depot/duty_list/<pk>/ ==> gives the duty list with that pk

    path('scheduler/depot/schedule/<int:pk>/', DepotScheduleViewSet.as_view({'get':'get_trips'}), name='schedule_trips'), 
    # GET /api/scheduler/depot/schedule/<pk>/ ==> get all the trips under a schedule 

    path('scheduler/depot/duty_list/update/<int:pk>/', DepotScheduleViewSet.as_view({'patch':'update_duty_list'}), name='update_duty_list'), 
    # PATCH /api/scheduler/depot/duty_list/<pk>/ ==> Update duty list information
]


# Include router to url pattern 
urlpatterns = [
    path('',include(router.urls) ), 
    path('',include(custom_urls) ), 
]
