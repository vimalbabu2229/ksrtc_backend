from django.urls import path, include
from rest_framework.authtoken import views
from rest_framework import routers
from accounts.views import AuthViewSet
from depot.views import DepotViewSet, DepotEmployeeViewSet, DepotVehicleViewSet, DepotTripsViewSet
from employee.views import EmployeeProfileView
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

# ___________________________ EMPLOYEE ROUTERS _____________________________
router.register(r'employee/profile', EmployeeProfileView, basename='employee_profile')


urlpatterns = [
    path('',include(router.urls) )
]
