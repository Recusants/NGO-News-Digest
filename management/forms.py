# forms.py
from django import forms
from publisher.models import BlogPost, Category, Vacancy, Notice
from django.utils import timezone

from django import forms
from accounts.models import Subscriber



from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import password_validation
from accounts.models import User, TeamMember, SiteInfo

# ========== USER PROFILE FORMS ==========

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
                  'address', 'interests', 'twitter', 'facebook']  # Changed 'intrests' to 'interests'
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
            'interests': forms.TextInput(attrs={  # Changed 'intrests' to 'interests'
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
                raise forms.ValidationError(
                    "Please enter your current password to save changes."
                )
            if not self.request.user.check_password(password):
                raise forms.ValidationError("Current password is incorrect.")
        return password
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
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
            except forms.ValidationError as error:
                self.add_error('new_password', error)
        
        return cleaned_data

# ========== TEAM MEMBER FORMS ==========

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
        super().__init__(*args, **kwargs)
        # Only show users who don't already have team profiles
        if self.instance.pk:
            # For editing, include the current user
            self.fields['user'].queryset = User.objects.filter(
                models.Q(team_profile__isnull=True) | models.Q(pk=self.instance.user.pk)
            )
        else:
            # For creating, only users without team profiles
            self.fields['user'].queryset = User.objects.filter(team_profile__isnull=True)
    
    def clean_user(self):
        user = self.cleaned_data.get('user')
        if not self.instance.pk:  # Only check for new entries
            if TeamMember.objects.filter(user=user).exists():
                raise forms.ValidationError(
                    "This user already has a team profile. Please choose another user."
                )
        return user

# ========== SITE SETTINGS FORM ==========

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
            raise forms.ValidationError("A subscriber with this email already exists.")
        return email


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'snippet', 'content', 'category', 'thumbnail', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter story title',
                'required': True
            }),
            'snippet': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'maxlength': 500,
                'placeholder': 'Brief summary of your story (max 500 characters)',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control d-none',  # Hidden, will be populated by rich editor
                'rows': 10,
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            #'status': forms.HiddenInput(),  # We'll handle this in JavaScript
        }
    
    thumbnail = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file d-none',
            'accept': 'image/*'
        })
    )
    
    def clean_snippet(self):
        snippet = self.cleaned_data.get('snippet', '').strip()
        if len(snippet) > 500:
            raise forms.ValidationError("Snippet must be 500 characters or less.")
        return snippet
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        # Check if content is empty or just contains empty tags
        import re
        text_content = re.sub(r'<[^>]*>', '', content).strip()
        if not text_content:
            raise forms.ValidationError("Content is required.")
        return content


from django import forms
from django.utils import timezone
from publisher.models import Vacancy, Notice

class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = [
            'title', 'organization', 'description', 'location',
            'job_type', 'application_deadline', 'application_link',
            'is_active', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter vacancy title',
                'required': True
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter organization name',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter job description',
                'required': True
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter job location',
                'required': True
            }),
            'job_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'application_deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'application_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/apply'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_application_deadline(self):
        deadline = self.cleaned_data.get('application_deadline')
        if deadline and deadline < timezone.now().date():
            raise forms.ValidationError("Application deadline cannot be in the past.")
        return deadline
    
    def clean_application_link(self):
        link = self.cleaned_data.get('application_link', '').strip()
        if link and not link.startswith(('http://', 'https://')):
            raise forms.ValidationError("Please enter a valid URL starting with http:// or https://")
        return link

class NoticeForm(forms.ModelForm):
    clear_attachment = forms.BooleanField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = Notice
        fields = [
            'title', 'description', 'organization',
            'category', 'publish_date', 'attachment',
            'is_active', 'is_important'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter notice title',
                'required': True
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter organization name',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter notice description',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'publish_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_important': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Limit file size to 10MB
            max_size = 10 * 1024 * 1024  # 10MB in bytes
            if attachment.size > max_size:
                raise forms.ValidationError("File size must be less than 10MB.")
            
            # Validate file extensions
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            import os
            ext = os.path.splitext(attachment.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f"Allowed file types: {', '.join(allowed_extensions)}"
                )
        return attachment
    
    def save(self, commit=True):
        notice = super().save(commit=False)
        
        # Handle file clearing
        if self.cleaned_data.get('clear_attachment'):
            if notice.attachment:
                notice.attachment.delete(save=False)
            notice.attachment = None
        
        if commit:
            notice.save()
        
        return notice