from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Depot, Vehicle, Trip
from accounts.models import User
from .serializers import *

# _______________________ MANAGE DEPOT PROFILE _____________________________
class DepotViewSet(ViewSet):
    permission_classes = [ IsAuthenticated ]    

    # Create depot profile
    def create(self,request):
        user = request.user 
        if user.is_admin :
            data = request.data
            if not Depot.objects.filter(user=user).exists():
                serializer = DepotSerializer(data=data)
                if serializer.is_valid():
                    serializer.save(user=user)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else: # bad request error 
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error':'Depot already exists'}, status=status.HTTP_409_CONFLICT)
        else : # user is not an admin 
            return Response({'error': 'User has no permission'}, status=status.HTTP_401_UNAUTHORIZED)
        
    # Get depot details 
    def list(self, request):
        try:
            user = request.user
            depot = Depot.objects.get(user=user.id)
            serializer = DepotSerializer(depot)
            data = serializer.data.copy()
            data['email'] = request.user.email
            data['vehicles'] = Vehicle.objects.filter(depot=user.id).count()
            data['employees'] = Employee.objects.filter(depot=user.id, user__is_active=True).count()
            return Response(data, status=status.HTTP_200_OK)
        except Depot.DoesNotExist:
            return Response({'error': 'Depot profile does not exist. Create profile first..'}, status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated]) 
    def update_depot(self, request):
        try:
            depot = Depot.objects.get(user=request.user.id)
            serializer = DepotSerializer(depot, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Depot.DoesNotExist:
            return Response({'error': 'Depot does not exist'}, status=status.HTTP_404_NOT_FOUND)

# ____________________________MANAGE DEPOT EMPLOYEES ____________________________
class DepotEmployeeViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def _create(self, user, data):
        user_serializer = EmployeeUserSerializer(data=data)
        if user_serializer.is_valid():
            if not User.objects.filter(email=data['email']).exists():
                user_data = user_serializer.validated_data
                User.objects.create_user(email=user_data['email'], password=user_data['date_of_join'].strftime("%d-%m-%Y"))

            employee = User.objects.get(email=data['email'])
            data['user'] = employee.id
            data['depot'] = user.id

            profile_serializer = EmployeeProfileSerializer(data=data)
            if profile_serializer.is_valid():
                profile_serializer.save()
                return Response({'message': 'Employee created successfully'}, status=status.HTTP_201_CREATED)
            else:
                return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Accepts the value of is_active (True, or False)
    def _list(self, user, active):
        employees = Employee.objects.filter(depot=user.id, user__is_active=active)
        serializer = EmployeeProfileSerializer(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Create new employee
    def create(self, request):
        user = request.user 
        if user.is_admin :
            data = request.data.copy()
            return self._create(user, data)
        else : # user is not an admin 
            return Response({'error': 'User has no permission'}, status=status.HTTP_401_UNAUTHORIZED)

    # Get all the employees under this depot     
    def list(self, request):
        try:
            return self._list(request.user, True)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee does not exist'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get all the previous employees
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def previous_employees(self, request):
        try:
            return self._list(request.user, False)
        except Employee.DoesNotExist:
            return Response({'error': 'Unknown Error occurred '}, status=status.HTTP_404_NOT_FOUND)
    
    # Get the details of a particular employee 
    def retrieve(self,request, pk=None):
        try:
            employee = Employee.objects.get(pk=pk)
            serializer = EmployeeProfileSerializer(employee)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee does not exist'}, status=status.HTTP_404_NOT_FOUND)
    
    # Update an employee detail
    def partial_update(self, request, pk=None):
        try:
            employee = Employee.objects.get(pk=pk)
            serializer = EmployeeProfileSerializer(employee, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else :
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
    def destroy(self, request, pk=None):
        try :
            employee = User.objects.get(pk=pk)
            employee.is_active = False
            employee.save()
            return Response({'message': f'({employee.email})Employee removed successfully'}, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
# ____________________________MANAGE DEPOT VEHICLES _____________________________
class DepotVehicleViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Vehicle.objects.all()
    serializer_class = GetVehicleSerializer

    def _create(self, user, data):
        data['depot'] = user.id
        serializer = VehicleSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'successfully added new vehicle'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def _list(self, user, active):
        vehicles = Vehicle.objects.filter(depot=user.id, is_active=active)
        serializer = GetVehicleSerializer(vehicles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Create a new vehicle
    def create(self, request):
        user = request.user
        if user.is_admin :
            data = request.data.copy()
            return self._create(user, data)
        else:
            return Response({'error': 'User has no permission'}, status=status.HTTP_401_UNAUTHORIZED)
        
    # Get all the current vehicles under the depot
    def list(self, request):
        try:
            return self._list(request.user, True)
        except Vehicle.DoesNotExist:
            return Response({'error':'Unknown error occurred'}, status=status.HTTP_404_NOT_FOUND)
        
    # Get all the previous vehicles under the depot
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def previous_vehicles(self, request):
        try:
            return self._list(request.user, False)
        except Vehicle.DoesNotExist:
            return Response({'error':'Unknown error occurred'}, status=status.HTTP_404_NOT_FOUND)
        
    # Remove a vehicle 
    def destroy(self, request, pk=None): #, *args, **kwargs
        try:
            vehicle = Vehicle.objects.get(pk=pk)
            vehicle.is_active = False
            vehicle.save()
            return Response({'message': f'({vehicle.reg_no})Vehicle is removed successfully'},status=status.HTTP_200_OK)
        except Vehicle.DoesNotExist:
            return Response({'error': 'Vehicle does not exists'}, status=status.HTTP_404_NOT_FOUND)
      
# ________________________________MANAGE BUS ROUTES _______________________________
class DepotTripsViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Trip.objects.all()
    serializer_class = TripSerializer

    def _create(self, user, data):
        # data['depot'] = user.id
        serializer = TripSerializer(data=data)
        if serializer.is_valid():
            serializer.save(depot=Depot.objects.get(user=user.id))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def _list(self, user, active):
        if Depot.objects.filter(user=user.id).exists():
            trips = Trip.objects.filter(depot=user.id, is_active=active)
            serializer = TripSerializer(trips, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Depot does not exists'}, status=status.HTTP_404_NOT_FOUND)
        
    # Create a new trip
    def create(self, request, *args, **kwargs):
        try:
            return self._create(request.user, request.data.copy())
        except:
            return Response({'error': 'Unknown error'}, status=status.HTTP_400_BAD_REQUEST)
        
    # List all the current valid trips under the depot 
    def list(self, request):
        try:
            return self._list(request.user, True)
        except:
            return Response({'error':'Unknown error occurred'}, status=status.HTTP_400_BAD_REQUEST)
        
    # List all the deleted trips under the depot 
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def deleted(self, request):
        try:
            return self._list(request.user, False)
        except:
            return Response({'error':'Unknown error occurred'}, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, pk=None):
        try:
            trip = Trip.objects.get(pk=pk)
            trip.is_active = False
            trip.save()
            return Response({'message': f'({trip.id}, {trip.departure_place}-{trip.arrival_place}) Trip deleted successfully'}, status=status.HTTP_200_OK)
        except :
            return Response({'error':'Unknown error occurred while trying to delete the trip'}, status=status.HTTP_404_NOT_FOUND)
    
