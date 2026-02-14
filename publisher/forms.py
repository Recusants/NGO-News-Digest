from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import strip_tags
import re

from .models import Story, Vacancy, Notice, Category, GenericAttachment
from django.contrib.contenttypes.models import ContentType


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


class AttachmentForm(forms.ModelForm):
    """Form for individual attachment editing (optional)"""
    class Meta:
        model = GenericAttachment
        fields = ['file', 'order']
        widgets = {
            'order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'}),
        }


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

    class Meta:
        model = Story
        fields = [
            'headline',
            'snippet',
            'content',
            'read_time',
            'status',
            'thumbnail',
            'category',
            'attachments',
        ]
        widgets = {
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter story headline'
            }),
            'snippet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of the story'
            }),
            'content': RichTextWidget(attrs={
                'class': 'form-control',
                'rows': 15
            }),
            'read_time': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5 min read'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
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

    # --------------------
    # FIELD VALIDATIONS
    # --------------------

    def clean_headline(self):
        headline = self.cleaned_data.get('headline', '').strip()
        if len(headline) < 5:
            raise ValidationError('Headline must be at least 5 characters long.')
        return headline

    def clean_snippet(self):
        snippet = self.cleaned_data.get('snippet', '').strip()
        if len(snippet) < 10:
            raise ValidationError('Snippet must be at least 10 characters long.')
        if len(snippet) > 500:
            raise ValidationError('Snippet cannot exceed 500 characters.')
        return snippet

    def clean_content(self):
        content = self.cleaned_data.get('content', '')
        plain_text = strip_tags(content)
        if len(plain_text) < 50:
            raise ValidationError('Content must be at least 50 characters long.')
        return content

    def clean_read_time(self):
        read_time = self.cleaned_data.get('read_time', '').strip()
        if not re.match(
            r'^\d+\s*(min|minute|minutes)?\s*(read)?$',
            read_time,
            re.IGNORECASE
        ):
            raise ValidationError(
                'Enter a valid read time format (e.g., "5 min read").'
            )
        return read_time

    # --------------------
    # SAVE (NO AUTHOR LOGIC)
    # --------------------

    def save(self, commit=True):
        """
        IMPORTANT:
        - This form NEVER sets `author`
        - This form NEVER sets `published_at`
        - Those belong in the VIEW
        """
        story = super().save(commit=False)

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
            'title', 'organization', 'description', 'location',
            'job_type', 'application_deadline', 'application_link',
            'is_active', 'is_featured', 'expiration_date', 'attachments'
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
            'description': RichTextWidget(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Detailed job description, requirements, benefits...'
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
        self.instance = kwargs.get('instance', None)
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
        if len(title) < 5:
            raise ValidationError('Job title must be at least 5 characters long.')
        return title
    
    def clean_organization(self):
        organization = self.cleaned_data.get('organization')
        if len(organization) < 2:
            raise ValidationError('Please enter a valid organization name.')
        return organization
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        plain_text = strip_tags(description)
        if len(plain_text) < 50:
            raise ValidationError('Job description must be at least 50 characters long.')
        return description
    
    def clean_application_deadline(self):
        deadline = self.cleaned_data.get('application_deadline')
        if deadline and deadline < timezone.now().date():
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
            'headline', 'overview', 'description', 'organization',
            'category', 'publish_date', 'expiration_date',
            'is_active', 'is_important', 'attachments'
        ]
        widgets = {
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Notice headline/title'
            }),
            'overview': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of the notice'
            }),
            'description': RichTextWidget(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Full notice content'
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
        self.instance = kwargs.get('instance', None)
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
    
    def clean_headline(self):
        headline = self.cleaned_data.get('headline')
        if len(headline) < 5:
            raise ValidationError('Headline must be at least 5 characters long.')
        return headline
    
    def clean_overview(self):
        overview = self.cleaned_data.get('overview')
        if len(overview) < 10:
            raise ValidationError('Overview must be at least 10 characters long.')
        if len(overview) > 500:
            raise ValidationError('Overview cannot exceed 500 characters.')
        return overview
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        plain_text = strip_tags(description)
        if len(plain_text) < 20:
            raise ValidationError('Notice description must be at least 20 characters long.')
        return description
    
    def clean_organization(self):
        organization = self.cleaned_data.get('organization')
        if len(organization) < 2:
            raise ValidationError('Please enter a valid organization name.')
        return organization
    
    def clean_publish_date(self):
        publish_date = self.cleaned_data.get('publish_date')
        if publish_date and publish_date > timezone.now().date():
            # Future publish dates are allowed (for scheduling)
            pass
        return publish_date
    
    def clean_expiration_date(self):
        expiration = self.cleaned_data.get('expiration_date')
        publish_date = self.cleaned_data.get('publish_date')
        
        if expiration and publish_date:
            if expiration < publish_date:
                raise ValidationError('Expiration date cannot be before publish date.')
        
        return expiration
    
    def save(self, commit=True):
        notice = super().save(commit=False)
        
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
        if len(name) < 2:
            raise ValidationError('Category name must be at least 2 characters long.')
        
        # Check for duplicate categories (case-insensitive)
        qs = Category.objects.filter(name__iexact=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('A category with this name already exists.')
        
        return name


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