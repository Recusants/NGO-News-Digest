# models.py
from django.db import models
from ckeditor.fields import RichTextField
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import re


class GenericAttachment(models.Model):
    """
    Generic attachment model that can be linked to any model
    """
    # Generic foreign key fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # File field
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Simple file info (auto-generated)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(null=True, blank=True)  # in bytes
    file_type = models.CharField(max_length=50, blank=True)
    
    # Ordering
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'uploaded_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return self.file_name if self.file_name else "Attachment"
    
    def save(self, *args, **kwargs):
        # Auto-populate file_name, file_size, and file_type
        if self.file:
            if not self.file_name:
                import os
                self.file_name = os.path.basename(self.file.name)
            
            if not self.file_size:
                try:
                    self.file_size = self.file.size
                except (OSError, FileNotFoundError):
                    self.file_size = 0
            
            if not self.file_type:
                import os
                filename = self.file.name
                ext = os.path.splitext(filename)[1].lower()
                self.file_type = ext[1:] if ext.startswith('.') else ext
        
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """Human readable file size"""
        if not self.file_size:
            return "0 KB"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def is_image(self):
        """Check if file is an image"""
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
        return self.file_type.lower() in image_extensions
    
    def is_pdf(self):
        """Check if file is a PDF"""
        return self.file_type.lower() == 'pdf'
    
    def is_document(self):
        """Check if file is a document"""
        doc_extensions = ['doc', 'docx', 'txt', 'rtf', 'odt']
        return self.file_type.lower() in doc_extensions



class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name


class Story(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
    ]
    
    headline = models.CharField(max_length=200)
    snippet = models.CharField(max_length=500)
    content = RichTextField(blank=True, null=True)
    read_time = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Thumbnail and category fields
    thumbnail = models.ImageField(upload_to='blog_thumbnails/', null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    
    def extract_first_image(self):
        """Extract first image URL from content for use as thumbnail"""
        img_pattern = r'<img[^>]+src="([^">]+)"'
        matches = re.findall(img_pattern, str(self.content))
        
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

    def system_id(self):
        return f"A-{str(self.id).zfill(6)}"
    system_id = property(system_id)
    
    # Property to get all attachments for this story
    @property
    def attachments(self):
        content_type = ContentType.objects.get_for_model(Story)
        return GenericAttachment.objects.filter(
            content_type=content_type,
            object_id=self.id
        ).order_by('order', 'uploaded_at')
    
    def __str__(self):
        return self.headline



class Vacancy(models.Model):
    """Vacancies model with RichTextField and attachments"""
    # Only 3 types
    JOB_TYPES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
    ]
    
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200)
    organization_details = models.CharField(max_length=200)
    how_to_apply = RichTextField()
    description = RichTextField()
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='FULL_TIME')
    
    application_deadline = models.DateField()
    application_link = models.URLField(blank=True)  # Optional
    
    # Simple status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    expiration_date = models.DateField(null=True, blank=True)
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Property to get all attachments for this vacancy
    @property
    def attachments(self):
        content_type = ContentType.objects.get_for_model(Vacancy)
        return GenericAttachment.objects.filter(
            content_type=content_type,
            object_id=self.id
        ).order_by('order', 'uploaded_at')
    
    def __str__(self):
        return f"{self.title} - {self.organization}"
    
    def is_expired(self):
        """Check if vacancy has expired"""
        if self.expiration_date:
            return self.expiration_date < timezone.now().date()
        return False
    
    def days_until_deadline(self):
        """Days until application deadline"""
        if self.application_deadline:
            delta = self.application_deadline - timezone.now().date()
            return delta.days
        return None


class Notice(models.Model):
    """Notices model with RichTextField and attachments"""
    # Only 3 categories
    CATEGORIES = [
        ('EVENT', 'Event'),
        ('TENDER', 'Tender'),
        ('ANNOUNCEMENT', 'Announcement'),
    ]
    
    headline = models.CharField(max_length=200)  # Changed from 100 to 200
    overview = models.CharField(max_length=500)  # Changed from 200 to 500
    description = RichTextField()  # Changed to RichTextField
    contact_details = RichTextField()
    organization = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORIES, default='ANNOUNCEMENT')
    
    publish_date = models.DateField(default=timezone.now)
    expiration_date = models.DateField(null=True, blank=True)
    
    # Simple status
    is_active = models.BooleanField(default=True)
    is_important = models.BooleanField(default=False)  # Instead of pinned
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Property to get all attachments for this notice
    @property
    def attachments(self):
        content_type = ContentType.objects.get_for_model(Notice)
        return GenericAttachment.objects.filter(
            content_type=content_type,
            object_id=self.id
        ).order_by('order', 'uploaded_at')
    
    def __str__(self):
        return f"{self.headline} - {self.organization}"
    
    def is_expired(self):
        """Check if notice has expired"""
        if self.expiration_date:
            return self.expiration_date < timezone.now().date()
        return False
    
    def get_category_color(self):
        """Get bootstrap color for category badge"""
        colors = {
            'EVENT': 'success',
            'TENDER': 'warning',
            'ANNOUNCEMENT': 'info'
        }
        return colors.get(self.category, 'secondary')