from django.urls import path, include
from rest_framework.authtoken import views
from rest_framework import routers
from accounts.views import AuthViewSet

# ________________________AUTHENTICATION ROUTER________________________
# End points :
#   POST    /api/auth/login/ 
#   POST    /api/auth/logout/
#   PATCH   /api/auth/reset_password/
auth_router = routers.DefaultRouter()
auth_router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('',include(auth_router.urls) )
]
