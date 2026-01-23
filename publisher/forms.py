# forms.py
from django import forms
from .models import BlogPost, Vacancy, Notice
from django.utils import timezone




class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'thumbnail', 'category', 'status']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'status': forms.Select(choices=BlogPost.STATUS_CHOICES),
        }
        


class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = ['title', 'organization', 'description', 'location', 
                 'job_type', 'application_deadline', 'application_link',
                 'is_active', 'is_featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'application_deadline': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_application_deadline(self):
        deadline = self.cleaned_data['application_deadline']
        if deadline < timezone.now().date():
            raise forms.ValidationError("Deadline cannot be in the past")
        return deadline


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'description', 'organization', 'category', 
                 'publish_date', 'attachment', 'is_active', 'is_important']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'publish_date': forms.DateInput(attrs={'type': 'date'}),
        }