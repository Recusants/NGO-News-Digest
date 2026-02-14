# forms.py - UNIFIED VERSION
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import strip_tags
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import password_validation
from django.contrib.contenttypes.models import ContentType
import re

from .models import Story, Vacancy, Notice, Category, GenericAttachment
from accounts.models import User, TeamMember, SiteInfo, Subscriber


# ============================================
# CUSTOM WIDGETS AND FIELDS
# ============================================

class RichTextWidget(forms.Textarea):
    """Custom widget for RichTextField with CKEditor"""
    
    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        attrs['class'] = attrs.get('class', '') + ' ckeditor'
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)
    
    class Media:
        css = {
            'all': ('ckeditor/ckeditor.css',)
        }
        js = ('ckeditor/ckeditor.js',)


class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget for multiple file uploads"""
    allow_multiple_selected = True
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].update({'multiple': True})
        super().__init__(*args, **kwargs)


class MultipleFileField(forms.FileField):
    """Custom field for handling multiple files"""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)
    
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        
        if isinstance(data, (list, tuple)):
            result = []
            for file in data:
                if file:  # Only process non-empty files
                    try:
                        result.append(single_file_clean(file, initial))
                    except ValidationError as e:
                        # Add file name to error message
                        e.message = f"{file.name}: {e.message}"
                        raise e
            return result
        else:
            if data:
                return [single_file_clean(data, initial)]
        return []


# ============================================
# PUBLISHER FORMS (Story, Vacancy, Notice, Category)
# ============================================

class StoryForm(forms.ModelForm):
    """Form for creating/editing Stories"""
    attachments = MultipleFileField(
        required=False,
        label='Add Files',
        help_text='Hold Ctrl/Cmd to select multiple files. Max size: 10MB per file.'
    )
    
    delete_attachments = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Delete existing files'
    )
    
    clear_thumbnail = forms.BooleanField(
        required=False,
        label='Remove current thumbnail'
    )

    class Meta:
        model = Story
        fields = [
            'headline',
            'snippet',
            'content',
            'read_time',
            'thumbnail',
            'category',
        ]
        widgets = {
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter story headline'
            }),
            'snippet': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief summary (max 500 characters)'
            }),
            'content': RichTextWidget(attrs={
                'class': 'form-control',
                'rows': 15
            }),
            'read_time': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5 min read'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'read_time': 'Estimated reading time (e.g., "5 min read")',
            'thumbnail': 'Main image for the story. Recommended size: 1200x630px',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Existing attachments (safe access)
        if self.instance and self.instance.pk:
            attachments = getattr(self.instance, 'attachments', [])
            if attachments:
                self.fields['delete_attachments'].choices = [
                    (str(att.id), att.file_name) for att in attachments
                ]
            else:
                self.fields['delete_attachments'].widget = forms.HiddenInput()
        else:
            self.fields['delete_attachments'].widget = forms.HiddenInput()

        # Make thumbnail optional
        self.fields['thumbnail'].required = False

    # --------------------
    # FIELD VALIDATIONS
    # --------------------

    def clean_headline(self):
        headline = self.cleaned_data.get('headline', '').strip()
        if not headline:
            raise ValidationError('Headline is required.')
        if len(headline) < 5:
            raise ValidationError('Headline must be at least 5 characters long.')
        return headline

    def clean_snippet(self):
        snippet = self.cleaned_data.get('snippet', '').strip()
        if not snippet:
            raise ValidationError('Snippet is required.')
        if len(snippet) < 10:
            raise ValidationError('Snippet must be at least 10 characters long.')
        if len(snippet) > 500:
            raise ValidationError('Snippet cannot exceed 500 characters.')
        return snippet

    def clean_content(self):
        content = self.cleaned_data.get('content', '')
        if not content:
            raise ValidationError('Content is required.')
        plain_text = strip_tags(content)
        if len(plain_text) < 50:
            raise ValidationError('Content must be at least 50 characters long.')
        return content

    def clean_read_time(self):
        read_time = self.cleaned_data.get('read_time', '').strip()
        if not read_time:
            raise ValidationError('Read time is required.')
        if not re.match(
            r'^\d+\s*(min|minute|minutes)?\s*(read)?$',
            read_time,
            re.IGNORECASE
        ):
            raise ValidationError(
                'Enter a valid read time format (e.g., "5 min read").'
            )
        return read_time

    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get('thumbnail')
        if thumbnail:
            # Limit file size to 5MB
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if thumbnail.size > max_size:
                raise ValidationError("Thumbnail size must be less than 5MB.")
            
            # Validate image extensions
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            import os
            ext = os.path.splitext(thumbnail.name)[1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(
                    f"Allowed image types: {', '.join(allowed_extensions)}"
                )
        return thumbnail

    # --------------------
    # SAVE
    # --------------------

    def save(self, commit=True):
        """
        IMPORTANT:
        - This form NEVER sets `author`
        - This form NEVER sets `published_at`
        - Those belong in the VIEW
        """
        story = super().save(commit=False)

        # Handle thumbnail clearing
        if self.cleaned_data.get('clear_thumbnail'):
            if story.thumbnail:
                story.thumbnail.delete(save=False)
            story.thumbnail = None

        if commit:
            story.save()

            # Handle attachments
            files = self.cleaned_data.get('attachments', [])
            if files:
                from .utils.attachment_utils import attach_multiple_files_to_object
                attach_multiple_files_to_object(story, files)

            # Handle deletion of attachments
            delete_ids = self.cleaned_data.get('delete_attachments', [])
            if delete_ids:
                GenericAttachment.objects.filter(
                    id__in=delete_ids,
                    object_id=story.id
                ).delete()

        return story



# forms.py
class VacancyForm(forms.ModelForm):
    """Form for creating/editing Vacancies"""
    attachments = MultipleFileField(
        required=False,
        label='Add Files',
        help_text='Hold Ctrl/Cmd to select multiple files. Max size: 10MB per file.'
    )
    
    # For existing attachments management
    delete_attachments = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Delete existing files'
    )
    
    class Meta:
        model = Vacancy
        fields = [
            'title', 'organization', 'organization_details', 'description', 'location',
            'job_type', 'application_deadline', 'application_link', 'how_to_apply',
            'is_active', 'is_featured', 'expiration_date'
            # Note: 'author' is NOT in fields list - handled automatically
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Job title'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company/Organization name'
            }),
            'organization_details': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Additional organization details'
            }),
            'description': RichTextWidget(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Detailed job description, requirements, benefits...'
            }),
            'how_to_apply': RichTextWidget(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Instructions on how to apply...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., New York, NY or Remote'
            }),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'application_deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'application_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...'
            }),
            'expiration_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'application_deadline': 'Last day to apply for this position',
            'expiration_date': 'When this vacancy should be automatically deactivated (optional)',
            'application_link': 'URL where applicants can submit their applications',
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Get request from kwargs
        super().__init__(*args, **kwargs)
        
        # Populate delete_attachments choices for existing instance
        if self.instance and self.instance.pk:
            attachments = self.instance.attachments
            choices = [(str(att.id), att.file_name) for att in attachments]
            self.fields['delete_attachments'].choices = choices
            if not attachments:
                self.fields['delete_attachments'].widget = forms.HiddenInput()
        else:
            self.fields['delete_attachments'].widget = forms.HiddenInput()
        
        # Set initial date values in proper format
        if self.instance and self.instance.pk:
            if self.instance.application_deadline:
                self.initial['application_deadline'] = self.instance.application_deadline.strftime('%Y-%m-%d')
            if self.instance.expiration_date:
                self.initial['expiration_date'] = self.instance.expiration_date.strftime('%Y-%m-%d')
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise ValidationError('Job title is required.')
        if len(title) < 5:
            raise ValidationError('Job title must be at least 5 characters long.')
        return title
    
    def clean_organization(self):
        organization = self.cleaned_data.get('organization')
        if not organization:
            raise ValidationError('Organization name is required.')
        if len(organization) < 2:
            raise ValidationError('Please enter a valid organization name.')
        return organization
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise ValidationError('Job description is required.')
        plain_text = strip_tags(description)
        if len(plain_text) < 50:
            raise ValidationError('Job description must be at least 50 characters long.')
        return description
    
    def clean_application_deadline(self):
        deadline = self.cleaned_data.get('application_deadline')
        if not deadline:
            raise ValidationError('Application deadline is required.')
        if deadline < timezone.now().date():
            raise ValidationError('Application deadline cannot be in the past.')
        return deadline
    
    def clean_expiration_date(self):
        expiration = self.cleaned_data.get('expiration_date')
        deadline = self.cleaned_data.get('application_deadline')
        
        if expiration and deadline:
            if expiration < deadline:
                raise ValidationError('Expiration date cannot be before application deadline.')
        
        return expiration
    
    def clean_application_link(self):
        link = self.cleaned_data.get('application_link')
        if link and not link.startswith(('http://', 'https://')):
            link = 'https://' + link
        return link
    
    def save(self, commit=True):
        vacancy = super().save(commit=False)
        
        # AUTO-SET AUTHOR: Set author to current user for new vacancies
        if not vacancy.pk:  # This is a new vacancy
            if self.request and self.request.user:
                vacancy.author = self.request.user
        
        # For existing vacancies, author stays as is
        
        if commit:
            vacancy.save()
            
            # Handle file attachments
            files = self.cleaned_data.get('attachments', [])
            if files:
                from .utils.attachment_utils import attach_multiple_files_to_object
                attach_multiple_files_to_object(vacancy, files)
            
            # Handle deletion of existing attachments
            delete_ids = self.cleaned_data.get('delete_attachments', [])
            if delete_ids:
                GenericAttachment.objects.filter(id__in=delete_ids).delete()
        
        return vacancy


class NoticeForm(forms.ModelForm):
    """Form for creating/editing Notices"""
    attachments = MultipleFileField(
        required=False,
        label='Add Files',
        help_text='Hold Ctrl/Cmd to select multiple files. Max size: 10MB per file.'
    )
    
    # For existing attachments management
    delete_attachments = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Delete existing files'
    )
    
    class Meta:
        model = Notice
        fields = [
            'headline', 'overview', 'description', 'organization', 'contact_details',
            'category', 'publish_date', 'expiration_date',
            'is_active', 'is_important'
            # Note: 'author' is NOT in fields list - handled automatically
        ]
        widgets = {
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Notice headline/title'
            }),
            'overview': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief summary of the notice'
            }),
            'description': RichTextWidget(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Full notice content'
            }),
            'contact_details': RichTextWidget(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Contact information'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Issuing organization'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'publish_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiration_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_important': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'overview': 'Brief summary (max 500 characters)',
            'publish_date': 'When this notice should be published',
            'expiration_date': 'When this notice should be automatically deactivated (optional)',
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Get request from kwargs
        super().__init__(*args, **kwargs)
        
        # Populate delete_attachments choices for existing instance
        if self.instance and self.instance.pk:
            attachments = self.instance.attachments
            choices = [(str(att.id), att.file_name) for att in attachments]
            self.fields['delete_attachments'].choices = choices
            if not attachments:
                self.fields['delete_attachments'].widget = forms.HiddenInput()
        else:
            self.fields['delete_attachments'].widget = forms.HiddenInput()
        
        # Set initial date values in proper format
        if self.instance and self.instance.pk:
            if self.instance.publish_date:
                self.initial['publish_date'] = self.instance.publish_date.strftime('%Y-%m-%d')
            if self.instance.expiration_date:
                self.initial['expiration_date'] = self.instance.expiration_date.strftime('%Y-%m-%d')
    
    # ... (keep all clean methods as they are) ...
    
    def save(self, commit=True):
        notice = super().save(commit=False)
        
        # AUTO-SET AUTHOR: Set author to current user for new notices
        if not notice.pk:  # This is a new notice
            if self.request and self.request.user:
                notice.author = self.request.user
        
        # For existing notices, author stays as is
        
        if commit:
            notice.save()
            
            # Handle file attachments
            files = self.cleaned_data.get('attachments', [])
            if files:
                from .utils.attachment_utils import attach_multiple_files_to_object
                attach_multiple_files_to_object(notice, files)
            
            # Handle deletion of existing attachments
            delete_ids = self.cleaned_data.get('delete_attachments', [])
            if delete_ids:
                GenericAttachment.objects.filter(id__in=delete_ids).delete()
        
        return notice

        

class CategoryForm(forms.ModelForm):
    """Simple form for Category model"""
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise ValidationError('Category name is required.')
        if len(name) < 2:
            raise ValidationError('Category name must be at least 2 characters long.')
        
        # Check for duplicate categories (case-insensitive)
        qs = Category.objects.filter(name__iexact=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('A category with this name already exists.')
        
        return name


# ============================================
# ATTACHMENT FORMS
# ============================================

class AttachmentForm(forms.ModelForm):
    """Form for individual attachment editing (optional)"""
    class Meta:
        model = GenericAttachment
        fields = ['file', 'order']
        widgets = {
            'order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'}),
        }


class QuickAttachmentForm(forms.Form):
    """Simple form for quick file uploads (AJAX)"""
    file = forms.FileField(
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif'
        }),
        label='Select files'
    )
    
    content_type = forms.CharField(widget=forms.HiddenInput())
    object_id = forms.IntegerField(widget=forms.HiddenInput())
    
    def clean(self):
        cleaned_data = super().clean()
        content_type_id = cleaned_data.get('content_type')
        object_id = cleaned_data.get('object_id')
        
        # Validate content type exists
        try:
            ContentType.objects.get_for_id(content_type_id)
        except ContentType.DoesNotExist:
            raise ValidationError('Invalid content type.')
        
        return cleaned_data


class BulkAttachmentForm(forms.Form):
    """Form for bulk attachment upload/management"""
    files = MultipleFileField(
        required=True,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True
        }),
        label='Select multiple files'
    )
    object_type = forms.ChoiceField(
        choices=[
            ('story', 'Story'),
            ('vacancy', 'Vacancy'),
            ('notice', 'Notice'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Object Type'
    )
    object_id = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Object ID',
        help_text='Enter the ID of the object to attach files to'
    )


# ============================================
# ACCOUNTS FORMS (User, TeamMember, SiteInfo, Subscriber)
# ============================================

class UserProfileForm(forms.ModelForm):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password to save changes'
        }),
        required=False,
        help_text="Enter your current password to save profile changes"
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 
                  'address', 'interests', 'twitter', 'facebook']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Address'
            }),
            'interests': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your interests (comma separated)'
            }),
            'twitter': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Twitter username'
            }),
            'facebook': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Facebook username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        password = self.cleaned_data.get('current_password')
        if self.request and self.request.user and self.has_changed():
            if not password:
                raise ValidationError(
                    "Please enter your current password to save changes."
                )
            if not self.request.user.check_password(password):
                raise ValidationError("Current password is incorrect.")
        return password
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email is already in use.")
        return email


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current password'
        }),
        required=True
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password'
        }),
        required=True,
        help_text=password_validation.password_validators_help_text_html()
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        }),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if self.user and not self.user.check_password(current_password):
            self.add_error('current_password', "Current password is incorrect.")
        
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "New passwords do not match.")
        
        if new_password:
            try:
                password_validation.validate_password(new_password, self.user)
            except ValidationError as error:
                self.add_error('new_password', error)
        
        return cleaned_data


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['user', 'position', 'bio', 'twitter_url', 
                  'linkedin_url', 'display_order', 'is_active']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-control'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Position/Role'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Professional bio'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/username'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        from django.db.models import Q
        super().__init__(*args, **kwargs)
        # Only show users who don't already have team profiles
        if self.instance.pk:
            # For editing, include the current user
            self.fields['user'].queryset = User.objects.filter(
                Q(team_profile__isnull=True) | Q(pk=self.instance.user.pk)
            )
        else:
            # For creating, only users without team profiles
            self.fields['user'].queryset = User.objects.filter(team_profile__isnull=True)
    
    def clean_user(self):
        user = self.cleaned_data.get('user')
        if not self.instance.pk:  # Only check for new entries
            if TeamMember.objects.filter(user=user).exists():
                raise ValidationError(
                    "This user already has a team profile. Please choose another user."
                )
        return user


class SiteInfoForm(forms.ModelForm):
    class Meta:
        model = SiteInfo
        fields = ['about_us', 'mission', 'vision', 'contact_email', 
                  'contact_phone', 'address', 'facebook_url', 
                  'twitter_url', 'linkedin_url']
        widgets = {
            'about_us': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'About our organization'
            }),
            'mission': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Our mission statement'
            }),
            'vision': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Our vision'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@example.com'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Organization address'
            }),
            'facebook_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/yourpage'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/yourhandle'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/company/yourcompany'
            }),
        }


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['email', 'name', 'is_verified', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name',
                'required': True
            }),
            'is_verified': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if Subscriber.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError("A subscriber with this email already exists.")
        return email