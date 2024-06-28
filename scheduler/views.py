from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q
from django.core.exceptions import ValidationError
from .serializers import *
from depot.serializers import TripSerializer
from depot.models import Depot, Vehicle
from .models import DutyList, DutyListMapper
from employee.models import Employee

from .scheduler import ScheduleTrips, ScheduleCrew, ScheduleVehicles

class DepotScheduleViewSet(ViewSet):
    permission_classes=[IsAuthenticated]

    # create entries in TripSchedulerMapper for a schedule 
    def _set_trip_schedule_mapper(self, trips, schedule):
        for trip in trips:
            data = {
                'index': trip[0], 
                'trip': trip[1],
                'schedule': schedule.id,
            }
            if trip[2] != 'None':
                data['terminal_gap']= trip[2]
            else :
                data['terminal_gap']= '00:00:00'

            serializer = TripScheduleMapperSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                raise ValidationError(serializer.errors) 

    # generate schedule
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def generate_duty_list(self,request):

        # Check the request.data contains 'start_place'
        if not 'start_place' in request.data:
            return Response({'error': 'Missing required field `start_place`'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get depot admin id 
        user = request.user

        try:
            # create trip scheduler instance proving the start place for the schedule 
            # By default start_place is set to 'PSL'
            trip_scheduler = ScheduleTrips(request.data['start_place'])

            # grt valid trips of the depot  
            trips_queryset = Trip.objects.filter(depot=user.id, is_active=True, status=True)
            trips = TripSerializer(trips_queryset, many=True).data

            # pass the list of active drivers and conductors under depot 
            # for the crew scheduling 
            conductors = Employee.objects.filter(depot=user.id, user__is_active=True, on_leave=False, designation='c').values_list('user', flat=True)
            drivers = Employee.objects.filter(depot=user.id, user__is_active=True, on_leave=False, designation='d').values_list('user', flat=True)
            crew_scheduler = ScheduleCrew(conductors, drivers)

            # pass active vehicles for vehicle scheduling 
            vehicles = Vehicle.objects.filter(depot=user.id, is_active=True, is_available=True).values_list('id', flat=True)
            vehicle_scheduler = ScheduleVehicles(vehicles)

            # SCHEDULE TRIPS 
            # pass the trips to trip_scheduler to get the schedules 
            schedules = trip_scheduler.schedule(trips)
            if schedules:
                # Make all the existing DutyLists is_active = False
                DutyList.objects.filter(depot=user.id).update(is_active=False)

                # Create a new duty list 
                duty_list_serializer = DutyListSerializer(data=request.data)
                if duty_list_serializer.is_valid():
                    # Below is_active is forcefully made True , because it found that it is by default set 
                    # to False , even if the field is made default=True in models 
                    duty_list_instance = duty_list_serializer.save(depot=Depot.objects.get(pk=user.id), is_active=True)

                    # Iterate through each schedule in schedules 
                    for schedule in schedules:
                        schedule_serializer = ScheduleSerializer(data=schedule)
                        if schedule_serializer.is_valid():
                            # create new schedules 
                            schedule_instance = schedule_serializer.save()

                            # Create the entries in TripSchedulerMapper for this schedule 
                            self._set_trip_schedule_mapper(schedule['trips'], schedule_instance)


                            # CREATE DUTY LIST MAPPER 
                            # get conductor and driver 
                            conductor, driver = crew_scheduler.get_crew()
                            vehicle = vehicle_scheduler.get_vehicle(schedule_instance.start_time, schedule_instance.end_time)
                            duty_list_mapper_data = {
                                'schedule': schedule_instance.id,
                                'duty_list': duty_list_instance.id,
                                'conductor': conductor, 
                                'driver': driver,
                                'vehicle': vehicle,
                            }
                            duty_list_mapper_serializer = DutyListMapperSerializer(data= duty_list_mapper_data)
                            if duty_list_mapper_serializer.is_valid():
                                duty_list_mapper_serializer.save()
                                # return Response({'Success': duty_list_mapper_serializer.data}, status=status.HTTP_200_OK)
                            else:
                                return Response(duty_list_mapper_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                            
                        else:
                            return Response(schedule_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Successfully created new schedule 
                    return Response(DutyListSerializer(duty_list_instance).data, status=status.HTTP_201_CREATED)
                else:
                    return Response(duty_list_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Failed to generate a schedule'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e :
            return Response({'error':{str(e)}}, status=status.HTTP_400_BAD_REQUEST)
        
    # Get all the duty lists under the depot. This includes both active and inactive schedules  
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def get_duty_lists(self, request):
        user = request.user
        duty_lists = DutyList.objects.filter(depot=user.id)
        if duty_lists.exists():
            serializer = GetDutyListSerializer(duty_lists, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else :
            return Response({'error':'No DutyLists found under your depot'}, status=status.HTTP_404_NOT_FOUND)

    # Re-Schedule crew for already existing Duty list 
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def schedule_crew(self, request):
        user = request.user
        # Get the available conductors and drivers under this depot 
        conductors = Employee.objects.filter(depot=user.id, user__is_active=True, on_leave=False, designation='c').values_list('user', flat=True)
        drivers = Employee.objects.filter(depot=user.id, user__is_active=True, on_leave=False, designation='d').values_list('user', flat=True)

        # Check the availability of employees 
        if not conductors.exists():
            return Response({'error': 'Conductors are not available for a re-schedule'}, status=status.HTTP_404_NOT_FOUND)
        
        if not drivers.exists():
            return Response({'error': 'Drivers are not available for a re-schedule'}, status=status.HTTP_404_NOT_FOUND)
        
        # create a crew scheduler
        crew_scheduler = ScheduleCrew(conductors, drivers)

        # get current active duty list of the depot 
        duty_list = DutyList.objects.filter(is_active=True, depot=user.id)
        if not duty_list.exists():
            return Response({'error': 'No valid duty list exist for this depot . Please generate a duty list '}, status=status.HTTP_404_NOT_FOUND)

        # get all the duty list mapper entries of the duty list
        duty_list_mappers = DutyListMapper.objects.filter(duty_list=duty_list[0].id)
        if not duty_list_mappers.exists():
            return Response({'error': 'No duty list mapper objects found'}, status=status.HTTP_404_NOT_FOUND)
        
        # CREATE NEW DUTY LIST WITH RE-SCHEDULE
        duty_list_serializer = DutyListSerializer(data=request.data)
        if duty_list_serializer.is_valid():
            # make all existing duty lists is_active = False
            DutyList.objects.filter(depot=user.id).update(is_active=False)

            # create new duty list
            # Below is_active is forcefully made True , because it found that it is by default set 
            # to False , even if the field is made default=True in models 
            new_duty_list = duty_list_serializer.save(depot=Depot.objects.get(pk=user.id), is_active=True)

            for entry in duty_list_mappers:
                conductor, driver = crew_scheduler.get_crew()
                duty_list_mapper_data = {
                        'schedule': entry.schedule.id,
                        'duty_list': new_duty_list.id,
                        'conductor': conductor, 
                        'driver': driver,
                        'vehicle': entry.vehicle.id if entry.vehicle != None else None,
                            }
                duty_list_mapper_serializer = DutyListMapperSerializer(data= duty_list_mapper_data)
                if duty_list_mapper_serializer.is_valid():
                    duty_list_mapper_serializer.save()
                else:
                    return Response(duty_list_mapper_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            # Successfully re-scheduled employees
            return Response({'message': 'Employee re-schedule successfully completed', 'duty_list': DutyListSerializer(new_duty_list).data}, status=status.HTTP_201_CREATED)
        else:
            return Response(duty_list_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Re-Schedule vehicles for already existing Duty list
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated]) 
    def schedule_vehicles(self, request):
        user = request.user

        # get available vehicles under this depot 
        vehicles = Vehicle.objects.filter(depot=user.id, is_active=True, is_available=True).values_list('id', flat=True)

        # Check whether any vehicle is available 
        if not vehicles.exists():
            return Response({'error': 'No vehicles are available for re-schedule'}, status=status.HTTP_404_NOT_FOUND)
        
        # create a new vehicle scheduler  
        vehicle_scheduler = ScheduleVehicles(vehicles)

        # get current active duty list of the depot 
        duty_list = DutyList.objects.filter(is_active=True, depot=user.id)
        if not duty_list.exists():
            return Response({'error': 'No valid duty list exist for this depot . Please generate a duty list '}, status=status.HTTP_404_NOT_FOUND)

        # get all the duty list mapper entries of the duty list
        duty_list_mappers = DutyListMapper.objects.filter(duty_list=duty_list[0].id)
        if not duty_list_mappers.exists():
            return Response({'error': 'No duty list mapper objects found'}, status=status.HTTP_404_NOT_FOUND)
         
        # CREATE NEW DUTY LIST WITH RE-SCHEDULE
        duty_list_serializer = DutyListSerializer(data=request.data)
        if duty_list_serializer.is_valid():
            # make all existing duty lists is_active = False
            DutyList.objects.filter(depot=user.id).update(is_active=False)

            # create new duty list
            # Below is_active is forcefully made True , because it found that it is by default set 
            # to False , even if the field is made default=True in models 
            new_duty_list = duty_list_serializer.save(depot=Depot.objects.get(pk=user.id), is_active=True)

            # Iterate over current mappers to create modified ones 
            for entry in duty_list_mappers:
                vehicle = vehicle_scheduler.get_vehicle(entry.schedule.start_time, entry.schedule.end_time)
                duty_list_mapper_data = {
                        'schedule': entry.schedule.id,
                        'duty_list': new_duty_list.id,
                        'conductor': entry.conductor.user if entry.conductor != None else None, 
                        'driver': entry.driver.user if entry.driver != None else None,
                        'vehicle': vehicle,
                            }
                duty_list_mapper_serializer = DutyListMapperSerializer(data= duty_list_mapper_data)
                if duty_list_mapper_serializer.is_valid():
                    duty_list_mapper_serializer.save()
                else:
                    return Response(duty_list_mapper_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            # Successfully re-scheduled vehicles 
            return Response({'message': 'Vehicle re-schedule successfully completed', 'duty_list': DutyListSerializer(new_duty_list).data}, status=status.HTTP_201_CREATED)
        else:
            return Response(duty_list_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Get the complete duty list . If pk is None , then the current active (latest)
    # duty list will be returned. ** Used a custom url mapper for below method **
    def duty_list(self, request, pk=None):
        user = request.user 
        try:
            if pk == None:
                duty_list = DutyList.objects.filter(depot=user.id, is_active=True)[0]
            else:
                duty_list = DutyList.objects.get(pk=pk)

            if duty_list:
                # get the duty list information
                duty_list_serializer = GetDutyListSerializer(duty_list)

                schedules = DutyListMapper.objects.filter(duty_list=duty_list.id)
                schedules_serializer = GetDutyListMapperSerializer(schedules, many=True)

                return Response({
                    'duty_list': duty_list_serializer.data, 
                    'schedules': schedules_serializer.data,
                                 }, status=status.HTTP_200_OK)
            else :
                return Response({'error': 'Duty list does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'error': f'Failed to retrieve a valid duty list'}, status=status.HTTP_404_NOT_FOUND)
        
    # Get all the trips in a schedule 
    # ** Used a custom url mapper for below method **
    def get_trips(self, request, pk=None):
        if pk != None:
            schedule_mapper = TripSchedulerMapper.objects.filter(schedule=pk)
            serializer = TripScheduleMapperSerializer(schedule_mapper, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error':'Please provide id of the schedule'}, status=status.HTTP_400_BAD_REQUEST)
        
    # Update duty list information 
    def update_duty_list(self, request, pk=None):
        if pk != None:
            try:
                duty_list = DutyList.objects.get(pk=pk)
                serializer = DutyListSerializer(duty_list, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except :
                return Response({'error': 'Duty list not found'}, status=status.HTTP_404_NOT_FOUND)
        else :
            return Response({'error':'Please provide id of the schedule'}, status=status.HTTP_400_BAD_REQUEST)
        
class EmployeeScheduleViewSet(ViewSet):
    permission_classes=[IsAuthenticated]

    # Get the trip associated with an employee
    def list(self, request):
        user = request.user
        if Employee.objects.get(user=user.id).on_leave:
            return Response({'error': 'Enjoy your leave days '}, status=status.HTTP_404_NOT_FOUND)
        # get the active duty mapper entry for the employee 
        duty_list_mapper_entry = DutyListMapper.objects.filter(Q(conductor=user.id) | Q(driver=user.id), duty_list__is_active = True)
        if not duty_list_mapper_entry.exists():
            return Response({'error': 'A valid schedule cannot be found for you'}, status=status.HTTP_404_NOT_FOUND)

        schedule_serializer = GetEmployeeScheduleSerializer(duty_list_mapper_entry[0])

        return Response(schedule_serializer.data, status=status.HTTP_200_OK)
