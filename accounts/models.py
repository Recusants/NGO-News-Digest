from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from datetime import datetime, date, timezone
from django.utils.timezone import localdate

import uuid


'''
CLASSES HERE:
    User
    Subscriber
'''
class User(AbstractUser):
    ROLES = {
        ('auther','auther'),
    }
    phone_number = models.CharField(max_length=30)
    address = models.TextField(max_length=255)
    roles = models.CharField(max_length=1000)
    intrests = models.CharField(max_length=1000)
    twitter = models.CharField(max_length=50, blank=True, null=True)
    facebook = models.CharField(max_length=50, blank=True, null=True)
    created_by = models.ForeignKey('User', on_delete=models.DO_NOTHING, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)





class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    # token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    verification_token = models.CharField(max_length=50, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-subscribed_at']
        
    def __str__(self):
        return f"{self.name} ({self.email})"
    


class SiteInfo(models.Model):
    """Store about us and contact information"""
    about_us = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    
    # Contact information
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Social media
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Last updated
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Site Information"
    
    def __str__(self):
        return "Site Information"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.id = 1
        super().save(*args, **kwargs)


class TeamMember(models.Model):
    """Team member profiles using User model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team_profile')
    position = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    
    # Social links
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Display order
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['display_order', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"