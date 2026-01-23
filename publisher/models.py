from django.db import models
from ckeditor.fields import RichTextField
from accounts.models import User
from django.utils import timezone

from django.utils.html import strip_tags

import re

class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Add these fields for thumbnails
    thumbnail = models.ImageField(upload_to='blog_thumbnails/', null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    
    def extract_first_image(self):
        """Extract first image URL from content for use as thumbnail"""
        import re
        # Look for img tags in content
        img_pattern = r'<img[^>]+src="([^">]+)"'
        matches = re.findall(img_pattern, self.content)
        
        if matches:
            return matches[0]  # Return first image URL
        return None
    
    def get_thumbnail_url(self):
        """Get thumbnail URL - prefers uploaded thumbnail, falls back to first image in content"""
        if self.thumbnail:
            return self.thumbnail.url
        
        # Try to extract first image from content
        first_image = self.extract_first_image()
        if first_image:
            return first_image
        
        # Default thumbnail
        return '/static/default-story.jpg'
    
    def __str__(self):
        return self.title






class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    def __str__(self):
        return self.name



class Vacancy(models.Model):
    """Simplified vacancies model"""
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    
    # Only 3 types
    JOB_TYPES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
    ]
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='FULL_TIME')
    
    application_deadline = models.DateField()
    application_link = models.URLField(blank=True)  # Optional
    
    # Simple status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.organization}"
    
    def days_remaining(self):
        """Calculate days until deadline"""
        remaining = (self.application_deadline - timezone.now().date()).days
        return max(0, remaining)


class Notice(models.Model):
    """Simplified notices model"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    organization = models.CharField(max_length=200)
    
    # Only 3 categories
    CATEGORIES = [
        ('EVENT', 'Event'),
        ('TENDER', 'Tender'),
        ('ANNOUNCEMENT', 'Announcement'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORIES, default='ANNOUNCEMENT')
    
    publish_date = models.DateField(default=timezone.now)
    
    # Optional file attachment
    attachment = models.FileField(upload_to='notices/', blank=True, null=True)
    
    # Simple status
    is_active = models.BooleanField(default=True)
    is_important = models.BooleanField(default=False)  # Instead of pinned
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_important', '-created_at']
    
    def __str__(self):
        return self.title