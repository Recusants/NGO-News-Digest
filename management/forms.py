# forms.py
from django import forms
from publisher.models import BlogPost, Category

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