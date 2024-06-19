from django.db import models
from django.contrib.auth.models import UserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("You haven't provided valid email")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        return self._create_user(email, password, **extra_fields)
    
#________________________ CUSTOM USER MODEL _______________________
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(blank=True, default='', unique=True)

    # is_active field is used to define whether a user is active or not . The relevance 
    # of this flag is that - in order to keep a proper history of all the data present 
    # in the system, the deletion of records are not allowed, instead the is_active flag 
    # can be made False which effectively counts the user as deleted.   
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    date_created = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'

#________________________DEPOT MODEL____________________________
class Depot(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    office = models.CharField(max_length=50)
    ato = models.CharField(max_length=50)
    district = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.office

#________________________EMPLOYEE MODEL____________________________
class Employee(models.Model):
    EMPLOYEE_TYPE = [
        ('d', 'Driver'),
        ('c', 'Conductor')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=50)
    pen_number = models.CharField(max_length=50)
    phone_number = PhoneNumberField(blank=True, unique=True, region='IN')
    designation = models.CharField(choices=EMPLOYEE_TYPE, max_length=2)
    date_of_join = models.DateField()
    on_leave = models.BooleanField(default=False)
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        return self.name