# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from .models import User, TeamMember

# --------------------------------------------------------------
# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, TeamMember

class UserForm(forms.ModelForm):
    """Form for creating/editing users (admin only)"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        required=False,
        help_text="Leave blank to keep existing password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'roles', 'phone_number', 'address', 'is_active'
        ]
        widgets = {
            'roles': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['password'].help_text = "Leave blank to keep existing password"
        else:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """Form for users to edit their own profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class TeamMemberForm(forms.ModelForm):
    """Form for team member profiles"""
    class Meta:
        model = TeamMember
        fields = [
            'prefix', 'position', 'department', 'location',
            'bio', 'head_shot', 'twitter_url', 'linkedin_url',
            'facebook_url', 'display_order', 'is_active'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'prefix': forms.TextInput(attrs={'placeholder': 'Mr/Ms/Dr etc.'}),
            'position': forms.TextInput(attrs={'placeholder': 'e.g., Executive Director'}),
        }






























































































        

class CustomAuthenticationForm(AuthenticationForm):
    """Login form with Bootstrap styling"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'phone_number', 'address']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TeamMemberProfileForm(forms.ModelForm):
    """Form for updating team member profile"""
    class Meta:
        model = TeamMember
        fields = ['prefix', 'position', 'department', 'location', 'bio',
                  'head_shot', 'twitter_url', 'linkedin_url', 'facebook_url']
        widgets = {
            'prefix': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Bootstrap styling"""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Current password'})
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'})
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )