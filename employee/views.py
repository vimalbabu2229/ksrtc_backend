from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet,ViewSet
from rest_framework import status
from rest_framework.permissions import IsAuthenticated 
from .models import Employee, LeaveApplication
from .serializers import ProfileSerializer, LeaveApplicationSerializer, LeaveListSerializer

class EmployeeProfileView(ViewSet):
    permission_classes=[IsAuthenticated]

    def list(self, request):
        user = request.user
        if user.is_active:
            try:
                data = Employee.objects.get(user=user.id)
                serializer = ProfileSerializer(data)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Employee.DoesNotExist:
                return Response({'error': 'Employee profile does not exist'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'You are not an active user . Please contact deport admin'}, status=status.HTTP_401_UNAUTHORIZED)

class LeaveApplicationView(ViewSet):
    permission_classes=[IsAuthenticated]

    # Create new leave application
    def create(self, request):
        serializer = LeaveApplicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=Employee.objects.get(pk=request.user.id))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # List all the leave applications 
    def list(self, request):
        user = request.user 

        leave_list = LeaveApplication.objects.filter(employee=user.id).order_by('-applied_on')
        serializer = LeaveListSerializer(leave_list, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Retrieve a particular leave application details 
    def retrieve(self, request, pk=None):
        try:
            leave = LeaveApplication.objects.get(pk=pk)
            serializer = LeaveApplicationSerializer(leave)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except :
            return Response({'error': 'Cannot find requested application'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Employee can delete a leave application, before admin review it 
    def destroy(self, request, pk=None):
        try:
            leave = LeaveApplication.objects.get(pk=pk)
            if leave.admin_read:
                return Response({'error': 'You cannot delete an application already reviewed by admin'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                leave.delete()
                return Response({'message':f'Deleted leave application for {leave.leave_type}'}, status=status.HTTP_200_OK)
        except :
            return Response({'error': 'Cannot find requested application'}, status=status.HTTP_400_BAD_REQUEST)