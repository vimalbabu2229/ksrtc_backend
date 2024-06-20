from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone

class CustomUserManager(BaseUserManager):
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

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(email, password, **extra_fields)
    
#________________________ CUSTOM USER MODEL _______________________
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)

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