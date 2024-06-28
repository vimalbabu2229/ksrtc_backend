from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import pandas as pd
from .models import Depot, Vehicle, Trip
from accounts.models import User
from employee.models import LeaveApplication
from .serializers import *

# __________________________ PROCESS DATASETS _____________________________
class ProcessDataset:
    def __init__(self, data) -> None:
        self.data = data

    # Set the boolean fields
    def _status_boolean(self, value):
        mapping = {'true': True, 'false':False, 'yes': True, 'no': False}
        value = value.lower()
        mapped_value = mapping.get(value)
        if isinstance(mapped_value, bool):
            return mapped_value
        else :
            raise ValueError(f" Expected values are ('yes', 'no', 'true', 'false'), but got something else ")
    
    # Check the unique fields 
    def _is_unique(self, df, field):
        return not df.duplicated(subset=[field]).any()
    
    # Get the pandas DataFrame 
    def _get_df(self):
        serializer = DataSetSerializer(data=self.data)
        if serializer.is_valid():
            dataset = self.data['dataset']
            try:
                return pd.read_excel(dataset, dtype=str)
            except:
                raise ValidationError(f'Uploaded dataset({dataset.name}) cannot be read')
        else :
            raise ValidationError(serializer.errors['dataset'])
    
    # Process employee DataFrame
    def process_employee(self):
        df = self._get_df()
        try :
            df['on_leave'] = df['on_leave'].apply(self._status_boolean)
        except ValueError as e:
            error = str(e).strip("['']")
            raise ValidationError({"on_leave": error})
        
        # Check the unique fields contain duplicate values 
        if not self._is_unique(df, 'email'):
            raise IntegrityError('(email)field contains duplicate entries')
        if not self._is_unique(df, 'pen_number'):
            raise IntegrityError('(pen_number)field contains duplicate entries')
        if not self._is_unique(df, 'phone_number'):
            raise IntegrityError('(phone_number) field contains duplicate entries')
        return df 
    
    # process vehicles DataFrame
    def process_vehicles(self):
        df = self._get_df()
        try:
            df['is_available'] = df['is_available'].apply(self._status_boolean)
        except ValueError as e:
            error = str(e).strip("['']")
            raise ValidationError({"is_available": error})
        
        # Check unique fields contain duplicate values 
        if not self._is_unique(df, 'reg_no'):
            raise IntegrityError('(reg_no)field contains duplicate entries')
        
        return df
    
    # process trips DataFrame
    def process_trips(self):
        df = self._get_df()
        return df

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
        profile_serializer = EmployeeProfileSerializer(data=data)

        if user_serializer.is_valid():
            if profile_serializer.is_valid():
                if not User.objects.filter(email=data['email']).exists():
                    user_data = user_serializer.validated_data
                    User.objects.create_user(email=user_data['email'], password=user_data['date_of_join'].strftime("%d-%m-%Y"))
                employee = User.objects.get(email=data['email'])
                if not Employee.objects.filter(user=employee.id).exists():
                    depot = Depot.objects.get(user=user.id)
                    profile_serializer.save(user=employee , depot=depot)
                    return profile_serializer.data
                else:
                    raise IntegrityError(f'({employee.user.email})Employee already exists')
            else:
                raise ValidationError(profile_serializer.errors)
        else:
            raise ValidationError(user_serializer.errors)
    
    # Accepts the value of is_active (True, or False)
    def _list(self, user, active):
        employees = Employee.objects.filter(depot=user.id, user__is_active=active)
        serializer = GetEmployeeProfileSerializer(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Create new employee
    def create(self, request):
        user = request.user 
        if user.is_admin :
            try:
                data = request.data.copy()
                serializer_data = self._create(user, data)
                return Response(serializer_data, status=status.HTTP_201_CREATED)
            
            except ValidationError as e:
                error = str(e).strip("['']")
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

            except IntegrityError as e:
                error = str(e).strip("['']")
                return Response({'error': error}, status=status.HTTP_409_CONFLICT)

            
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
    def deleted_employees(self, request):
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
            employee = Employee.objects.filter(pk=pk, user__is_active=True)[0]
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
        
    # Import the data set of employees
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def import_dataset(self, request):
        try:
            processor = ProcessDataset(request.data)
            employee_df = processor.process_employee()
            # Validate data completely before saving 
            for row in employee_df.iterrows():
                user_serializer = UserExistValidatorSerializer(data=dict(row[1]))
                profile_serializer = EmployeeProfileSerializer(data=dict(row[1]))
                if user_serializer.is_valid():
                    if profile_serializer.is_valid():
                        continue
                    else:
                        return Response({'row': (row[0] + 2), 'error':profile_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'row': (row[0] + 2), 'error':user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            # save data to database
            for row in employee_df.iterrows():
                self._create(request.user, dict(row[1]))
                
            return Response({'message': f'Employee dataset imported successfully'}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            error = str(e).strip("['']")
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        
        except IntegrityError as e:
            error = str(e).strip("['']")
            return Response({'error': error}, status=status.HTTP_409_CONFLICT)
       
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
        
    # Import data set of vehicles
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def import_dataset(self, request):
        try:
            processor = ProcessDataset(request.data)
            vehicle_df = processor.process_vehicles()
            # Validate data completely before saving 
            for row in vehicle_df.iterrows():
                serializer = VehicleSerializer(data=dict(row[1]))
                if serializer.is_valid():
                    continue
                else:
                    return Response({'row': (row[0] + 2), 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
               
            # save data to database
            for row in vehicle_df.iterrows():
                self._create(request.user, dict(row[1]))
                
            return Response({'message': f'Vehicle dataset imported successfully'}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            error = str(e).strip("['']")
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        
        except IntegrityError as e:
            error = str(e).strip("['']")
            return Response({'error': error}, status=status.HTTP_409_CONFLICT)
    
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
        
    # Import data set of trips
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def import_dataset(self, request):
        try:
            processor = ProcessDataset(request.data)
            vehicle_df = processor.process_trips()
            # Validate data completely before saving 
            for row in vehicle_df.iterrows():
                serializer = TripSerializer(data=dict(row[1]))
                if serializer.is_valid():
                    continue
                else:
                    return Response({'row': (row[0] + 2), 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
               
            # save data to database
            for row in vehicle_df.iterrows():
                self._create(request.user, dict(row[1]))
                
            return Response({'message': f'Trips dataset imported successfully'}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            error = str(e).strip("['']")
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        
        except IntegrityError as e:
            error = str(e).strip("['']")
            return Response({'error': error}, status=status.HTTP_409_CONFLICT)

# ________________________________ LEAVE APPLICATIONS _______________________________
class DepotLeaveApplicationsView(ViewSet):
    permission_classes=[IsAuthenticated]

    # List leave applications under this depot 
    def list(self, request):
        user = request.user
        leave = LeaveApplication.objects.filter(employee__depot = user.id).order_by('-applied_on')
        serializer = LeaveListSerializer(leave,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Retrieve specific leave application details
    def retrieve(self, request, pk=None):
        try:
            leave = LeaveApplication.objects.get(pk=pk)
            leave.admin_read = True
            leave.save()

            serializer = LeaveDetailsSerializer(leave)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'Cannot find requested application'}, status=status.HTTP_400_BAD_REQUEST)
