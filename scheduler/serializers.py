from rest_framework import serializers
from .models import *
from depot.serializers import TripSerializer

class DutyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyList
        fields = ['id', 'name', 'created_at', 'description', 'is_active']

# Used to retrieve all the duty lists under the depot including active and inactive
# This is for the purpose of showing the list of duty lists 
class GetDutyListSerializer(serializers.ModelSerializer):
    class Meta :
        model = DutyList
        fields =['id', 'name', 'is_active']

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'

class TripScheduleMapperSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripSchedulerMapper
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        trip_serializer = TripSerializer(instance.trip)
        representation['trip'] = trip_serializer.data
        return representation

class DutyListMapperSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyListMapper
        fields = '__all__'

class GetDutyListMapperSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyListMapper
        fields =['driver', 'conductor', 'vehicle', 'schedule']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['driver'] = {'id':instance.driver.user_id, 'name':instance.driver.name}
        representation['conductor'] = {'id': instance.conductor.user_id, 'name': instance.conductor.name}
        representation['vehicle'] = {'id': instance.vehicle.id,'reg_no':instance.vehicle.reg_no}
        representation['schedule'] = ScheduleSerializer(instance.schedule).data
        
        return representation

class GetEmployeeScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyListMapper
        fields =['driver', 'conductor', 'vehicle', 'schedule']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['schedule'] = ScheduleSerializer(instance.schedule).data
        representation['driver'] = {'id':instance.driver.user_id, 'name':instance.driver.name}
        representation['conductor'] = {'id': instance.conductor.user_id, 'name': instance.conductor.name}
        representation['vehicle'] = {'id': instance.vehicle.id,'reg_no':instance.vehicle.reg_no}
        trips = TripSchedulerMapper.objects.filter(schedule=instance.schedule.id)
        representation['trips'] = TripScheduleMapperSerializer(trips, many=True).data
        
        return representation
    
