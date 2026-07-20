from django.db import models 
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('vendor', 'Vendor'),
    )
    
    role = models.CharField(max_length=20, choices = ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.username
    
class StudentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    matric_number = models.CharField(
        max_length=20,
        unique=True
    )

    department = models.CharField(
        max_length=100
    )

    level = models.CharField(
        max_length=20
    )
    
    
class Address(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    hostel = models.CharField(max_length=100)

    room_number = models.CharField(max_length=20)
    
class UserActivity(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    action = models.CharField(max_length=200)

    timestamp = models.DateTimeField(
        auto_now_add=True
    )