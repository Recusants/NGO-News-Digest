# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction
from django.http import JsonResponse, Http404
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
import json

from django.views.generic import ListView
from django.db.models import Count
from django.utils import timezone

from publisher.models import Story, Vacancy, Notice, Category, GenericAttachment
from publisher.forms import (
    StoryForm, VacancyForm, NoticeForm, CategoryForm,
    QuickAttachmentForm, BulkAttachmentForm
)
from publisher.utils.attachment_utils import attach_multiple_files_to_object


# ============================================
# STORY VIEWS
# ============================================

@login_required
def story_create(request):
    """Create a new story"""
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            story = form.save()
            messages.success(request, f'Story "{story.headline}" created successfully!')
            return redirect('story_detail', pk=story.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StoryForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Story',
        'submit_text': 'Create Story',
    }
    return render(request, 'management/story_form.html', context)


@login_required
def story_edit(request, pk):
    """Edit an existing story"""
    story = get_object_or_404(Story, pk=pk)
    
    # Permission check: only author or superuser can edit
    if not (request.user.is_superuser or story.author == request.user):
        messages.error(request, 'You do not have permission to edit this story.')
        return redirect('story_detail', pk=story.pk)
    
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES, instance=story, user=request.user)
        if form.is_valid():
            story = form.save()
            messages.success(request, f'Story "{story.headline}" updated successfully!')
            return redirect('story_detail', pk=story.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StoryForm(instance=story, user=request.user)
    
    context = {
        'form': form,
        'story': story,
        'title': f'Edit Story: {story.headline}',
        'submit_text': 'Update Story',
    }
    return render(request, 'management/story_form.html', context)


class StoryCreateView(LoginRequiredMixin, CreateView):
    """Class-based view for creating stories"""
    model = Story
    form_class = StoryForm
    template_name = 'management/story_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Story "{form.instance.headline}" created successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Story'
        context['submit_text'] = 'Create Story'
        return context
    
    def get_success_url(self):
        return reverse_lazy('story_detail', kwargs={'pk': self.object.pk})


class StoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Class-based view for editing stories"""
    model = Story
    form_class = StoryForm
    template_name = 'management/story_form.html'
    
    def test_func(self):
        """Only author or superuser can edit"""
        story = self.get_object()
        return self.request.user.is_superuser or story.author == self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Story "{form.instance.headline}" updated successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Story: {self.object.headline}'
        context['submit_text'] = 'Update Story'
        return context
    
    def get_success_url(self):
        return reverse_lazy('story_detail', kwargs={'pk': self.object.pk})


# ============================================
# VACANCY VIEWS
# ============================================

@login_required
@permission_required('core.add_vacancy', raise_exception=True)
def vacancy_create(request):
    """Create a new vacancy"""
    if request.method == 'POST':
        form = VacancyForm(request.POST, request.FILES)
        if form.is_valid():
            vacancy = form.save()
            messages.success(request, f'Vacancy "{vacancy.title}" created successfully!')
            return redirect('vacancy_detail', pk=vacancy.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VacancyForm()
    
    context = {
        'form': form,
        'title': 'Create New Vacancy',
        'submit_text': 'Create Vacancy',
    }
    return render(request, 'management/vacancy_form.html', context)


@login_required
@permission_required('core.change_vacancy', raise_exception=True)
def vacancy_edit(request, pk):
    """Edit an existing vacancy"""
    vacancy = get_object_or_404(Vacancy, pk=pk)
    
    if request.method == 'POST':
        form = VacancyForm(request.POST, request.FILES, instance=vacancy)
        if form.is_valid():
            vacancy = form.save()
            messages.success(request, f'Vacancy "{vacancy.title}" updated successfully!')
            return redirect('vacancy_detail', pk=vacancy.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VacancyForm(instance=vacancy)
    
    context = {
        'form': form,
        'vacancy': vacancy,
        'title': f'Edit Vacancy: {vacancy.title}',
        'submit_text': 'Update Vacancy',
    }
    return render(request, 'management/vacancy_form.html', context)


class VacancyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Class-based view for creating vacancies"""
    model = Vacancy
    form_class = VacancyForm
    template_name = 'management/vacancy_form.html'
    
    def test_func(self):
        return self.request.user.has_perm('core.add_vacancy')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Vacancy "{form.instance.title}" created successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Vacancy'
        context['submit_text'] = 'Create Vacancy'
        return context
    
    def get_success_url(self):
        return reverse_lazy('vacancy_detail', kwargs={'pk': self.object.pk})


class VacancyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Class-based view for editing vacancies"""
    model = Vacancy
    form_class = VacancyForm
    template_name = 'management/vacancy_form.html'
    
    def test_func(self):
        return self.request.user.has_perm('core.change_vacancy')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Vacancy "{form.instance.title}" updated successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Vacancy: {self.object.title}'
        context['submit_text'] = 'Update Vacancy'
        return context
    
    def get_success_url(self):
        return reverse_lazy('vacancy_detail', kwargs={'pk': self.object.pk})


# ============================================
# NOTICE VIEWS
# ============================================

@login_required
@permission_required('core.add_notice', raise_exception=True)
def notice_create(request):
    """Create a new notice"""
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save()
            messages.success(request, f'Notice "{notice.headline}" created successfully!')
            return redirect('notice_detail', pk=notice.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = NoticeForm()
    
    context = {
        'form': form,
        'title': 'Create New Notice',
        'submit_text': 'Create Notice',
    }
    return render(request, 'management/notice_form.html', context)


@login_required
@permission_required('core.change_notice', raise_exception=True)
def notice_edit(request, pk):
    """Edit an existing notice"""
    notice = get_object_or_404(Notice, pk=pk)
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES, instance=notice)
        if form.is_valid():
            notice = form.save()
            messages.success(request, f'Notice "{notice.headline}" updated successfully!')
            return redirect('notice_detail', pk=notice.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = NoticeForm(instance=notice)
    
    context = {
        'form': form,
        'notice': notice,
        'title': f'Edit Notice: {notice.headline}',
        'submit_text': 'Update Notice',
    }
    return render(request, 'management/notice_form.html', context)


class NoticeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Class-based view for creating notices"""
    model = Notice
    form_class = NoticeForm
    template_name = 'management/notice_form.html'
    
    def test_func(self):
        return self.request.user.has_perm('core.add_notice')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Notice "{form.instance.headline}" created successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Notice'
        context['submit_text'] = 'Create Notice'
        return context
    
    def get_success_url(self):
        return reverse_lazy('notice_detail', kwargs={'pk': self.object.pk})


class NoticeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Class-based view for editing notices"""
    model = Notice
    form_class = NoticeForm
    template_name = 'management/notice_form.html'
    
    def test_func(self):
        return self.request.user.has_perm('core.change_notice')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Notice "{form.instance.headline}" updated successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Notice: {self.object.headline}'
        context['submit_text'] = 'Update Notice'
        return context
    
    def get_success_url(self):
        return reverse_lazy('notice_detail', kwargs={'pk': self.object.pk})


# ============================================
# CATEGORY VIEWS
# ============================================

@login_required
@permission_required('core.add_category', raise_exception=True)
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Create New Category',
        'submit_text': 'Create Category',
    }
    return render(request, 'management/category_form.html', context)


@login_required
@permission_required('core.change_category', raise_exception=True)
def category_edit(request, pk):
    """Edit an existing category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': f'Edit Category: {category.name}',
        'submit_text': 'Update Category',
    }
    return render(request, 'management/category_form.html', context)


class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Class-based view for creating categories"""
    model = Category
    form_class = CategoryForm
    template_name = 'management/category_form.html'
    success_url = reverse_lazy('category_list')
    
    def test_func(self):
        return self.request.user.has_perm('core.add_category')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Category "{form.instance.name}" created successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Category'
        context['submit_text'] = 'Create Category'
        return context


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Class-based view for editing categories"""
    model = Category
    form_class = CategoryForm
    template_name = 'management/category_form.html'
    success_url = reverse_lazy('category_list')
    
    def test_func(self):
        return self.request.user.has_perm('core.change_category')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Category "{form.instance.name}" updated successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Category: {self.object.name}'
        context['submit_text'] = 'Update Category'
        return context


# ============================================
# ATTACHMENT VIEWS (AJAX/API)
# ============================================

@login_required
def quick_attachment_upload(request):
    """AJAX endpoint for quick file uploads"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = QuickAttachmentForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                content_type = ContentType.objects.get_for_id(
                    int(form.cleaned_data['content_type'])
                )
                object_id = form.cleaned_data['object_id']
                
                # Get the model class and object
                model_class = content_type.model_class()
                obj = get_object_or_404(model_class, pk=object_id)
                
                # Check permissions
                if not can_edit_object(request.user, obj):
                    return JsonResponse({
                        'success': False,
                        'error': 'Permission denied'
                    }, status=403)
                
                # Process files
                files = request.FILES.getlist('file')
                attachments = []
                
                for file in files:
                    attachment = GenericAttachment(
                        content_object=obj,
                        file=file
                    )
                    attachment.save()
                    attachments.append({
                        'id': attachment.id,
                        'name': attachment.file_name,
                        'url': attachment.file.url,
                        'size': attachment.get_file_size_display(),
                        'type': attachment.file_type,
                        'is_image': attachment.is_image()
                    })
                
                return JsonResponse({
                    'success': True,
                    'attachments': attachments,
                    'message': f'{len(attachments)} file(s) uploaded successfully'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
        
        else:
            errors = form.errors.as_json()
            return JsonResponse({
                'success': False,
                'errors': json.loads(errors)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
def bulk_attachment_upload(request):
    """Bulk upload attachments to an object"""
    if request.method == 'POST':
        form = BulkAttachmentForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                object_type = form.cleaned_data['object_type']
                object_id = form.cleaned_data['object_id']
                files = form.cleaned_data['files']
                
                # Get the object based on type
                if object_type == 'story':
                    obj = get_object_or_404(Story, pk=object_id)
                    perm_required = 'core.change_story'
                elif object_type == 'vacancy':
                    obj = get_object_or_404(Vacancy, pk=object_id)
                    perm_required = 'core.change_vacancy'
                elif object_type == 'notice':
                    obj = get_object_or_404(Notice, pk=object_id)
                    perm_required = 'core.change_notice'
                else:
                    messages.error(request, 'Invalid object type.')
                    return redirect('dashboard')
                
                # Check permissions
                if not request.user.has_perm(perm_required):
                    messages.error(request, 'You do not have permission to edit this object.')
                    return redirect('dashboard')
                
                # Attach files
                attachments = attach_multiple_files_to_object(obj, files)
                
                messages.success(
                    request, 
                    f'Successfully uploaded {len(attachments)} file(s) to {obj}'
                )
                
                # Redirect to object detail page
                if object_type == 'story':
                    return redirect('story_detail', pk=object_id)
                elif object_type == 'vacancy':
                    return redirect('vacancy_detail', pk=object_id)
                elif object_type == 'notice':
                    return redirect('notice_detail', pk=object_id)
                
            except Exception as e:
                messages.error(request, f'Error uploading files: {str(e)}')
        
        else:
            messages.error(request, 'Please correct the errors below.')
    
    else:
        form = BulkAttachmentForm()
    
    context = {
        'form': form,
        'title': 'Bulk Upload Attachments',
        'submit_text': 'Upload Files',
    }
    return render(request, 'management/bulk_upload_form.html', context)


@login_required
def delete_attachment(request, attachment_id):
    """Delete a specific attachment"""
    attachment = get_object_or_404(GenericAttachment, id=attachment_id)
    
    # Get the parent object
    obj = attachment.content_object
    
    # Check permissions
    if not can_edit_object(request.user, obj):
        messages.error(request, 'You do not have permission to delete this attachment.')
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    
    # Store info for message
    file_name = attachment.file_name
    obj_type = obj.__class__.__name__.lower()
    
    # Delete the attachment
    attachment.delete()
    
    messages.success(request, f'Attachment "{file_name}" deleted successfully.')
    
    # Redirect back to object detail or edit page
    if obj_type == 'story':
        return redirect('story_detail', pk=obj.pk)
    elif obj_type == 'vacancy':
        return redirect('vacancy_detail', pk=obj.pk)
    elif obj_type == 'notice':
        return redirect('notice_detail', pk=obj.pk)
    
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def reorder_attachments(request):
    """AJAX endpoint for reordering attachments"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            attachment_ids = data.get('attachment_ids', [])
            
            with transaction.atomic():
                for index, attachment_id in enumerate(attachment_ids):
                    attachment = GenericAttachment.objects.get(
                        id=attachment_id,
                        content_type__model=data.get('model'),
                        object_id=data.get('object_id')
                    )
                    
                    # Check permissions
                    obj = attachment.content_object
                    if not can_edit_object(request.user, obj):
                        return JsonResponse({
                            'success': False,
                            'error': 'Permission denied'
                        }, status=403)
                    
                    attachment.order = index
                    attachment.save()
            
            return JsonResponse({'success': True})
            
        except GenericAttachment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Attachment not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


# views.py - Add these delete views

# Story Delete View
class StoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Story
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('story_list')
    
    def test_func(self):
        story = self.get_object()
        return self.request.user.is_superuser or story.author == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Story deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Vacancy Delete View
class VacancyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Vacancy
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('vacancy_list')
    
    def test_func(self):
        return self.request.user.has_perm('core.delete_vacancy')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Vacancy deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Notice Delete View
class NoticeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Notice
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('notice_list')
    
    def test_func(self):
        return self.request.user.has_perm('core.delete_notice')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Notice deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Category Delete View
class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Category
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('category_list')
    
    def test_func(self):
        return self.request.user.has_perm('core.delete_category')
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        
        # Check if category has stories
        if category.story_set.count() > 0:
            messages.error(request, f'Cannot delete category "{category.name}" because it has {category.story_set.count()} story/stories.')
            return redirect('category_list')
        
        messages.success(request, f'Category "{category.name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)

# OR Function-based view for category delete
@login_required
@permission_required('core.delete_category', raise_exception=True)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        # Check if category has stories
        story_count = category.story_set.count()
        if story_count > 0:
            messages.error(request, f'Cannot delete category "{category.name}" because it has {story_count} story/stories.')
            return redirect('category_list')
        
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('category_list')
    
    # GET request - show confirmation
    context = {
        'object': category,
        'object_type': 'category',
        'object_name': category.name,
        'back_url': reverse_lazy('category_list'),
    }
    return render(request, 'management/confirm_delete.html', context)

# ============================================
# HELPER FUNCTIONS
# ============================================

def can_edit_object(user, obj):
    """Check if user can edit the given object"""
    if user.is_superuser:
        return True
    
    if isinstance(obj, Story):
        return obj.author == user
    elif isinstance(obj, Vacancy):
        return user.has_perm('core.change_vacancy')
    elif isinstance(obj, Notice):
        return user.has_perm('core.change_notice')
    elif isinstance(obj, Category):
        return user.has_perm('core.change_category')
    
    return False


def get_edit_url_for_object(obj):
    """Get the appropriate edit URL for an object"""
    obj_type = obj.__class__.__name__.lower()
    
    if obj_type == 'story':
        return reverse_lazy('story_edit', kwargs={'pk': obj.pk})
    elif obj_type == 'vacancy':
        return reverse_lazy('vacancy_edit', kwargs={'pk': obj.pk})
    elif obj_type == 'notice':
        return reverse_lazy('notice_edit', kwargs={'pk': obj.pk})
    elif obj_type == 'category':
        return reverse_lazy('category_edit', kwargs={'pk': obj.pk})
    
    return None


# ============================================
# MIXED DASHBOARD/OVERVIEW VIEWS
# ============================================

@login_required
def dashboard(request):
    """User dashboard showing their content"""
    context = {
        'user_stories': Story.objects.filter(author=request.user).order_by('-created_at')[:5],
        'recent_vacancies': Vacancy.objects.filter(is_active=True).order_by('-created_at')[:5],
        'recent_notices': Notice.objects.filter(is_active=True).order_by('-created_at')[:5],
        'categories': Category.objects.all()[:10],
    }
    return render(request, 'management/dashboard.html', context)


@login_required
def my_content(request):
    """Show all content created by the user"""
    context = {
        'stories': Story.objects.filter(author=request.user).order_by('-created_at'),
        'vacancies': Vacancy.objects.all().order_by('-created_at') if request.user.has_perm('core.view_vacancy') else [],
        'notices': Notice.objects.all().order_by('-created_at') if request.user.has_perm('core.view_notice') else [],
    }
    return render(request, 'management/my_content.html', context)


class StoryListView(LoginRequiredMixin, ListView):
    model = Story
    template_name = 'management/story_list.html'
    context_object_name = 'stories'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Story.objects.all().select_related('author', 'category')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'DRAFT':
            queryset = queryset.filter(status='DRAFT')
        elif status == 'PUBLISHED':
            queryset = queryset.filter(status='PUBLISHED')
        
        # Filter by author (my stories)
        if self.request.GET.get('mine') == 'true':
            queryset = queryset.filter(author=self.request.user)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = Story.objects.count()
        context['published_count'] = Story.objects.filter(status='PUBLISHED').count()
        context['draft_count'] = Story.objects.filter(status='DRAFT').count()
        context['attachment_count'] = GenericAttachment.objects.filter(
            content_type=ContentType.objects.get_for_model(Story)
        ).count()
        return context


class VacancyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Vacancy
    template_name = 'management/vacancy_list.html'
    context_object_name = 'vacancies'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.has_perm('core.view_vacancy')
    
    def get_queryset(self):
        queryset = Vacancy.objects.all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'expired':
            queryset = queryset.filter(expiration_date__lt=timezone.now().date())
        elif status == 'featured':
            queryset = queryset.filter(is_featured=True)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now().date()
        context['total_count'] = Vacancy.objects.count()
        context['active_count'] = Vacancy.objects.filter(is_active=True).count()
        context['expired_count'] = Vacancy.objects.filter(
            expiration_date__lt=now
        ).count()
        context['featured_count'] = Vacancy.objects.filter(is_featured=True).count()
        return context


class NoticeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Notice
    template_name = 'management/notice_list.html'
    context_object_name = 'notices'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.has_perm('core.view_notice')
    
    def get_queryset(self):
        queryset = Notice.objects.all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'expired':
            queryset = queryset.filter(expiration_date__lt=timezone.now().date())
        
        # Filter by category
        category = self.request.GET.get('category')
        if category in ['EVENT', 'TENDER', 'ANNOUNCEMENT']:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('-publish_date', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = Notice.objects.count()
        context['active_count'] = Notice.objects.filter(is_active=True).count()
        context['important_count'] = Notice.objects.filter(is_important=True).count()
        context['attachment_count'] = GenericAttachment.objects.filter(
            content_type=ContentType.objects.get_for_model(Notice)
        ).count()
        context['now'] = timezone.now()
        return context


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'management/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.annotate(
            story_count=Count('story')
        ).order_by('name')



# views.py - Add these helper views

@login_required
def story_publish(request, pk):
    story = get_object_or_404(Story, pk=pk)
    
    if not (request.user.is_superuser or story.author == request.user):
        messages.error(request, 'You do not have permission to publish this story.')
        return redirect('story_detail', pk=story.pk)
    
    story.status = 'PUBLISHED'
    story.published_at = timezone.now()
    story.save()
    
    messages.success(request, f'Story "{story.headline}" published successfully!')
    return redirect('story_detail', pk=story.pk)

@login_required
def story_unpublish(request, pk):
    story = get_object_or_404(Story, pk=pk)
    
    if not (request.user.is_superuser or story.author == request.user):
        messages.error(request, 'You do not have permission to unpublish this story.')
        return redirect('story_detail', pk=story.pk)
    
    story.status = 'DRAFT'
    story.save()
    
    messages.success(request, f'Story "{story.headline}" unpublished successfully!')
    return redirect('story_detail', pk=story.pk)

@login_required
@permission_required('core.change_vacancy', raise_exception=True)
def vacancy_activate(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    vacancy.is_active = True
    vacancy.save()
    messages.success(request, f'Vacancy "{vacancy.title}" activated!')
    return redirect('vacancy_detail', pk=vacancy.pk)

@login_required
@permission_required('core.change_vacancy', raise_exception=True)
def vacancy_deactivate(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    vacancy.is_active = False
    vacancy.save()
    messages.success(request, f'Vacancy "{vacancy.title}" deactivated!')
    return redirect('vacancy_detail', pk=vacancy.pk)

@login_required
@permission_required('core.change_vacancy', raise_exception=True)
def vacancy_feature(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    vacancy.is_featured = True
    vacancy.save()
    messages.success(request, f'Vacancy "{vacancy.title}" marked as featured!')
    return redirect('vacancy_detail', pk=vacancy.pk)

@login_required
@permission_required('core.change_vacancy', raise_exception=True)
def vacancy_unfeature(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    vacancy.is_featured = False
    vacancy.save()
    messages.success(request, f'Vacancy "{vacancy.title}" removed from featured!')
    return redirect('vacancy_detail', pk=vacancy.pk)

@login_required
@permission_required('core.change_notice', raise_exception=True)
def notice_activate(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    notice.is_active = True
    notice.save()
    messages.success(request, f'Notice "{notice.headline}" activated!')
    return redirect('notice_detail', pk=notice.pk)

@login_required
@permission_required('core.change_notice', raise_exception=True)
def notice_deactivate(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    notice.is_active = False
    notice.save()
    messages.success(request, f'Notice "{notice.headline}" deactivated!')
    return redirect('notice_detail', pk=notice.pk)

@login_required
@permission_required('core.change_notice', raise_exception=True)
def notice_mark_important(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    notice.is_important = True
    notice.save()
    messages.success(request, f'Notice "{notice.headline}" marked as important!')
    return redirect('notice_detail', pk=notice.pk)

@login_required
@permission_required('core.change_notice', raise_exception=True)
def notice_unmark_important(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    notice.is_important = False
    notice.save()
    messages.success(request, f'Notice "{notice.headline}" removed from important!')
    return redirect('notice_detail', pk=notice.pk)