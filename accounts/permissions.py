from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from depot.models import Depot

class IsAdmin(BasePermission):
    """
    A class to validate whether the user have admin privileges  
    """
    def has_permission(self, request, view):
        if request.user.is_admin:
            return True
        else:
            raise PermissionDenied(detail='You dont have admin privileges')
        

class IsActive(BasePermission):
    """
    A class to validate whether the user is an active user 
    """
    
    def has_permission(self, request, view):
        if request.user.is_active:
            return True
        else:
            raise PermissionDenied(detail='You are not an active user')
        
class hasProfile(BasePermission):
    """
    A class to validate whether a depot admin has a profile created .
    Admin are allowed to do anything in the system only after the 
    creation of a valid profile
    """

    def has_permission(self, request, view):
        if Depot.objects.filter(user=request.user).exists():
            return True
        
        else:
            raise PermissionDenied(detail='Depot profile has not created . Create profile and try again ')