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
    


from django.db import models
from django.core.validators import MinValueValidator

class SiteInfo(models.Model):
    """Store comprehensive site information for about page and contact"""
    
    # Hero Section
    organization_name = models.CharField(max_length=200, default="NGO News Digest")
    tagline = models.CharField(max_length=300, default="Amplifying Civil Society Impact in Zimbabwe")
    company_logo = models.URLField(blank=True, default="")
    favicon = models.URLField(blank=True, default="")
    
    # About Content
    about_us = models.TextField(blank=True, default="NGO News Digest is a Zimbabwe-based news and media initiative dedicated to sharing, amplifying, and celebrating the work of non-governmental organisations operating across Zimbabwe.")
    
    # Mission & Vision
    mission = models.TextField(blank=True, default="To document, share, and elevate the work of NGOs in Zimbabwe through timely, impactful, and comprehensive coverage that connects grassroots initiatives with national development goals.")
    vision = models.TextField(blank=True, default="To be Zimbabwe's premier platform for celebrating and amplifying civil society impact, serving as the definitive repository of positive change and development innovation.")
    
    # What We Do - Services
    service_1_title = models.CharField(max_length=100, blank=True, default="Impact Storytelling")
    service_1_description = models.TextField(blank=True, default="Document and share success stories that showcase the tangible impact of NGO work across Zimbabwe's communities.")
    
    service_2_title = models.CharField(max_length=100, blank=True, default="Career Hub")
    service_2_description = models.TextField(blank=True, default="Connect talented professionals with meaningful opportunities in Zimbabwe's civil society sector through our job portal.")
    
    service_3_title = models.CharField(max_length=100, blank=True, default="Notice Board")
    service_3_description = models.TextField(blank=True, default="Disseminate important announcements, funding opportunities, events, and policy updates affecting the NGO sector.")
    
    service_4_title = models.CharField(max_length=100, blank=True, default="Sector Networking")
    service_4_description = models.TextField(blank=True, default="Facilitate connections and collaboration between NGOs, donors, government agencies, and communities.")
    
    # Core Values
    values = models.JSONField(default=dict, blank=True)
    
    # Sectors covered (comma-separated)
    sectors_covered = models.TextField(blank=True, 
        default="Health & WASH,Agriculture & Food Security,Education & Skills Development,Livelihoods & Economic Empowerment,Gender & Protection,Climate Resilience,Governance & Accountability,Humanitarian Response,Youth & Child Development,Disability Inclusion")
    
    # Partner categories
    partners = models.TextField(blank=True,
        default="UN Agencies,International NGOs,Local NGOs,Government Ministries,Development Partners,Private Sector")
    
    # Contact information
    contact_email = models.EmailField(blank=True, default="contact@ngonewsdigest.co.zw")
    contact_phone = models.CharField(max_length=20, blank=True, default="+263 77 123 4567")
    address = models.TextField(blank=True, default="123 Development Avenue, Harare, Zimbabwe")
    
    # Social media
    facebook_url = models.URLField(blank=True, default="https://facebook.com/ngonewsdigest")
    twitter_url = models.URLField(blank=True, default="https://twitter.com/ngonewsdigest")
    linkedin_url = models.URLField(blank=True, default="https://linkedin.com/company/ngonewsdigest")
    instagram_url = models.URLField(blank=True, default="")
    youtube_url = models.URLField(blank=True, default="")
    
    # Additional settings
    show_statistics = models.BooleanField(default=True)
    show_partners = models.BooleanField(default=True)
    show_team_preview = models.BooleanField(default=True)
    
    # Last updated
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Site Information"
    
    def __str__(self):
        return self.organization_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.id = 1
        super().save(*args, **kwargs)

    @property
    def sectors_list(self):
        """Return sectors as a list - accessible as property in templates"""
        if not self.sectors:
            return []
        # Split by comma and clean up whitespace
        return [cat.strip() for cat in self.sectors.split(',') if cat.strip()]


    
    @classmethod
    def get_site_info(cls):
        """Get or create site info singleton"""
        obj, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'organization_name': 'NGO News Digest',
                'tagline': 'Amplifying Civil Society Impact in Zimbabwe'
            }
        )
        return obj
    
    @property
    def sectors_list(self):
        """Return sectors as list"""
        if not self.sectors_covered:
            return []
        return [s.strip() for s in self.sectors_covered.split(',')]
    
    @property
    def partners_list(self):
        """Return partners as list"""
        if not self.partners:
            return []
        return [p.strip() for p in self.partners.split(',')]



class TeamMember(models.Model):
    """Team member profiles using User model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team_profile')
    prefix = models.CharField(max_length=10)
    position = models.CharField(max_length=30)
    department = models.CharField(max_length=30)
    location = models.CharField(max_length=30)
    bio = models.TextField(blank=True)
    head_shot = models.ImageField(upload_to='team_head_shots/', null=True, blank=True)
    
    # Social links
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    
    # Display order
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    

    class Meta:
        ordering = ['display_order', 'user__first_name']

    def get_head_shot_url(self):
        if self.head_shot:
            return self.head_shot.url
        
        return '/static/default-head-shot.png'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"