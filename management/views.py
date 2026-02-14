# views.py - COMPLETE FILE (FUNCTION-BASED VIEWS ONLY)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
import json
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.utils.html import strip_tags
from django.utils import timezone

from django.db.models import Q
from publisher.models import Story, Vacancy, Notice, Category, GenericAttachment
from publisher.forms import StoryForm, VacancyForm, NoticeForm, CategoryForm
from publisher.utils.attachment_utils import attach_multiple_files_to_object





# views.py - UPDATED FUNCTIONS ONLY

# ============================================
# VACANCY VIEWS (Function-based)
# ============================================

@login_required
@permission_required('core.add_vacancy', raise_exception=True)
def vacancy_create(request):
    """Create a new vacancy"""
    if request.method == 'POST':
        form = VacancyForm(request.POST, request.FILES)
        if form.is_valid():
            # Set author manually before saving
            vacancy = form.save(commit=False)
            vacancy.author = request.user
            vacancy.save()
            
            # Now handle attachments
            files = request.FILES.getlist('attachments')
            if files:
                attach_multiple_files_to_object(vacancy, files)
            
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


# ============================================
# NOTICE VIEWS (Function-based)
# ============================================

@login_required
@permission_required('core.add_notice', raise_exception=True)
def notice_create(request):
    """Create a new notice"""
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            # Set author manually before saving
            notice = form.save(commit=False)
            notice.author = request.user
            notice.save()
            
            # Now handle attachments
            files = request.FILES.getlist('attachments')
            if files:
                attach_multiple_files_to_object(notice, files)
            
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


# ============================================
# STORY VIEWS (Function-based)
# ============================================



@login_required
def story_create(request):
    """Create a new story (draft or published)"""
    from publisher.views import notify_subscribers  # ADD THIS IMPORT
    
    if request.method == 'POST':
        is_draft = 'save_as_draft' in request.POST
        publish_now = 'publish_now' in request.POST

        form = StoryForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            story = form.save(commit=False)
            story.author = request.user  # Set author

            if publish_now:
                errors = []
                if not story.headline or len(story.headline.strip()) < 5:
                    errors.append('Headline must be at least 5 characters.')
                if not story.snippet or len(story.snippet.strip()) < 10:
                    errors.append('Snippet must be at least 10 characters.')
                if not story.content or len(strip_tags(story.content)) < 50:
                    errors.append('Content must be at least 50 characters.')
                if not story.read_time:
                    errors.append('Read time is required.')

                if errors:
                    for e in errors:
                        messages.error(request, e)
                    return render(request, 'management/story_form.html', {
                        'form': form,
                        'title': 'Create New Story',
                        'submit_text': 'Create Story',
                        'is_create': True,
                    })

                story.status = 'PUBLISHED'
                story.published_at = timezone.now()
                success_message = f'Story "{story.headline}" published successfully!'
                
                # Save the story
                story.save()
                
                # ✅ ADD THIS: Send email notifications
                notify_subscribers(story.id)
                messages.info(request, 'Email notifications are being sent to subscribers in the background.')
                
            else:
                story.status = 'DRAFT'
                if not story.headline:
                    story.headline = f"Draft Story - {timezone.now():%Y%m%d-%H%M}"
                if not story.read_time:
                    story.read_time = "5 min read"
                success_message = 'Story saved as draft successfully!'
                story.save()

            # Attachments
            for f in request.FILES.getlist('attachments'):
                GenericAttachment.objects.create(
                    content_object=story,
                    file=f
                )

            messages.success(request, success_message)
            return redirect('story_detail', pk=story.pk)

        # FORM INVALID
        if is_draft:
            try:
                story = Story.objects.create(
                    author=request.user,
                    status='DRAFT',
                    headline=request.POST.get(
                        'headline',
                        f"Draft Story - {timezone.now():%Y%m%d-%H%M}"
                    )[:200],
                    snippet=request.POST.get('snippet', '')[:500],
                    content=request.POST.get('content', ''),
                    read_time=request.POST.get('read_time', '5 min read')[:20],
                )

                category_id = request.POST.get('category')
                if category_id:
                    try:
                        story.category = Category.objects.get(pk=category_id)
                        story.save()
                    except Category.DoesNotExist:
                        pass

                if request.FILES.get('thumbnail'):
                    story.thumbnail = request.FILES['thumbnail']
                    story.save()

                for f in request.FILES.getlist('attachments'):
                    GenericAttachment.objects.create(
                        content_object=story,
                        file=f
                    )

                messages.success(request, 'Draft saved successfully!')
                return redirect('story_detail', pk=story.pk)

            except Exception as e:
                messages.error(request, f'Error saving draft: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = StoryForm(user=request.user)

    return render(request, 'management/story_form.html', {
        'form': form,
        'title': 'Create New Story',
        'submit_text': 'Create Story',
        'is_create': True,
    })




@login_required
def story_edit(request, pk):
    story = get_object_or_404(Story, pk=pk)
    from publisher.views import notify_subscribers  # ADD THIS IMPORT

    if not (request.user.is_superuser or story.author == request.user):
        messages.error(request, 'You do not have permission to edit this story.')
        return redirect('story_detail', pk=story.pk)

    if request.method == 'POST':
        is_draft = 'save_as_draft' in request.POST
        publish_now = 'publish_now' in request.POST

        form = StoryForm(request.POST, request.FILES, instance=story, user=request.user)

        if form.is_valid():
            story = form.save(commit=False)

            if publish_now:
                errors = []
                if not story.headline or len(story.headline.strip()) < 5:
                    errors.append('Headline must be at least 5 characters.')
                if not story.snippet or len(story.snippet.strip()) < 10:
                    errors.append('Snippet must be at least 10 characters.')
                if not story.content or len(strip_tags(story.content)) < 50:
                    errors.append('Content must be at least 50 characters.')
                if not story.read_time:
                    errors.append('Read time is required.')

                if errors:
                    for e in errors:
                        messages.error(request, e)
                    return render(request, 'management/story_form.html', {
                        'form': form,
                        'story': story,
                        'title': f'Edit Story: {story.headline}',
                        'submit_text': 'Update Story',
                        'is_create': False,
                    })

                story.status = 'PUBLISHED'
                if not story.published_at:
                    story.published_at = timezone.now()
                success_message = 'Story published successfully!'
                
                # Save the story
                story.save()
                
                # ✅ ADD THIS: Send email notifications
                notify_subscribers(story.id)
                messages.info(request, 'Email notifications are being sent to subscribers in the background.')
                
            elif is_draft:
                story.status = 'DRAFT'
                success_message = 'Draft saved successfully!'
            else:
                success_message = 'Story updated successfully!'

            if 'clear_thumbnail' in request.POST:
                if story.thumbnail:
                    story.thumbnail.delete(save=False)
                story.thumbnail = None

            story.save()

            for f in request.FILES.getlist('attachments'):
                GenericAttachment.objects.create(
                    content_object=story,
                    file=f
                )

            for att_id in request.POST.getlist('delete_attachments'):
                GenericAttachment.objects.filter(
                    id=att_id,
                    object_id=story.id
                ).delete()

            messages.success(request, success_message)
            return redirect('story_detail', pk=story.pk)

        # INVALID FORM BUT DRAFT
        if is_draft:
            if request.POST.get('headline'):
                story.headline = request.POST['headline'][:200]
            if request.POST.get('snippet'):
                story.snippet = request.POST['snippet'][:500]
            if request.POST.get('content'):
                story.content = request.POST['content']
            if request.POST.get('read_time'):
                story.read_time = request.POST['read_time'][:20]

            category_id = request.POST.get('category')
            if category_id:
                try:
                    story.category = Category.objects.get(pk=category_id)
                except Category.DoesNotExist:
                    pass

            story.status = 'DRAFT'
            story.save()

            if request.FILES.get('thumbnail'):
                story.thumbnail = request.FILES['thumbnail']
                story.save()

            if 'clear_thumbnail' in request.POST:
                if story.thumbnail:
                    story.thumbnail.delete(save=False)
                story.thumbnail = None
                story.save()

            for f in request.FILES.getlist('attachments'):
                GenericAttachment.objects.create(
                    content_object=story,
                    file=f
                )

            for att_id in request.POST.getlist('delete_attachments'):
                GenericAttachment.objects.filter(
                    id=att_id,
                    object_id=story.id
                ).delete()

            messages.success(request, 'Draft saved successfully!')
            return redirect('story_detail', pk=story.pk)

        messages.error(request, 'Please correct the errors below.')

    else:
        form = StoryForm(instance=story, user=request.user)

    return render(request, 'management/story_form.html', {
        'form': form,
        'story': story,
        'title': f'Edit Story: {story.headline}',
        'submit_text': 'Update Story',
        'is_create': False,
    })



# ============================================
# CATEGORY VIEWS (Function-based)
# ============================================

@login_required
@permission_required('core.add_category', raise_exception=True)
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)  # NO request parameter
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm()  # NO request parameter
    
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
        form = CategoryForm(request.POST, instance=category)  # NO request parameter
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm(instance=category)  # NO request parameter
    
    context = {
        'form': form,
        'category': category,
        'title': f'Edit Category: {category.name}',
        'submit_text': 'Update Category',
    }
    return render(request, 'management/category_form.html', context)




























































































































# ============================================
# STORY VIEWS (Function-based)
# ============================================



@login_required
def story_publish(request, pk):
    print('Engaged ')
    """Publish a draft story - with AJAX support"""
    from publisher.views import notify_subscribers  # ADD THIS IMPORT
    
    try:
        story = get_object_or_404(Story, pk=pk)
        
        # Permission check
        if not (request.user.is_superuser or story.author == request.user):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)
            messages.error(request, 'You do not have permission to publish this story.')
            return redirect('story_detail', pk=story.pk)
        
        # Validate required fields
        errors = []
        if not story.headline or len(story.headline.strip()) < 5:
            errors.append('Headline is required and must be at least 5 characters.')
        if not story.snippet or len(story.snippet.strip()) < 10:
            errors.append('Snippet is required and must be at least 10 characters.')
        if not story.content or len(story.content.strip()) < 50:
            errors.append('Content is required and must be meaningful.')
        if not story.read_time:
            errors.append('Read time is required.')
        
        if errors:
            error_message = ' '.join(errors)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_message})
            for error in errors:
                messages.error(request, error)
            return redirect('story_edit', pk=story.pk)
        
        # Publish the story
        story.status = 'PUBLISHED'
        if not story.published_at:
            story.published_at = timezone.now()
        story.save()
        
        # ✅ ADD THIS: Send email notifications
        notify_subscribers(story.id)
      
        email_message = ' Email notifications are being sent to subscribers.'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Story "{story.headline}" published successfully!{email_message}',
                'new_status': story.status,
                'new_status_display': story.get_status_display()
            })
        
        messages.success(request, f'Story "{story.headline}" published successfully!')
        messages.info(request, 'Email notifications are being sent to subscribers.')
        return redirect('story_detail', pk=story.pk)
        
    except Story.DoesNotExist:
        print('Ran Ex')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Story not found.'}, status=404)
        messages.error(request, 'Story not found.')
        return redirect('story_list')



@login_required
def story_unpublish(request, pk):
    """Unpublish a story (convert to draft) - with AJAX support"""
    try:
        story = get_object_or_404(Story, pk=pk)
        
        # Permission check
        if not (request.user.is_superuser or story.author == request.user):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)
            messages.error(request, 'You do not have permission to unpublish this story.')
            return redirect('story_detail', pk=story.pk)
        
        # Unpublish the story
        story.status = 'DRAFT'
        story.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Story "{story.headline}" unpublished successfully!',
                'new_status': story.status,
                'new_status_display': story.get_status_display()
            })
        
        messages.success(request, f'Story "{story.headline}" unpublished successfully!')
        return redirect('story_detail', pk=story.pk)
        
    except Story.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Story not found.'}, status=404)
        messages.error(request, 'Story not found.')
        return redirect('story_list')

@login_required
def story_delete(request, pk):
    """Function-based story delete view - with AJAX support"""
    try:
        story = get_object_or_404(Story, pk=pk)
        
        # Permission check
        if not (request.user.is_superuser or story.author == request.user):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)
            messages.error(request, 'You do not have permission to delete this story.')
            return redirect('story_detail', pk=story.pk)
        
        if request.method == 'POST':
            story_title = story.headline
            
            # Get counts before deletion for AJAX response
            total_before = Story.objects.count()
            published_before = Story.objects.filter(status='PUBLISHED').count()
            draft_before = Story.objects.filter(status='DRAFT').count()
            
            story.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Story "{story_title}" deleted successfully!',
                    'deleted_id': pk,
                    'new_counts': {
                        'total': total_before - 1,
                        'published': published_before - (1 if story.status == 'PUBLISHED' else 0),
                        'draft': draft_before - (1 if story.status == 'DRAFT' else 0),
                    }
                })
            
            messages.success(request, f'Story "{story_title}" deleted successfully!')
            return redirect('story_list')
        
        # GET request - show confirmation (non-AJAX)
        context = {
            'object': story,
            'object_type': 'story',
            'object_name': story.headline,
            'back_url': reverse_lazy('story_detail', kwargs={'pk': story.pk}),
        }
        return render(request, 'management/confirm_delete.html', context)
        
    except Story.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Story not found.'}, status=404)
        messages.error(request, 'Story not found.')
        return redirect('story_list')


@login_required
def story_detail(request, pk):
    """View story details (READ-ONLY)"""
    story = get_object_or_404(
        Story.objects.select_related('author', 'category'), 
        pk=pk
    )
    
    # Check if user has permission to view (author, superuser, or published)
    if story.status != 'PUBLISHED' and not (request.user.is_superuser or story.author == request.user):
        messages.error(request, 'You do not have permission to view this story.')
        return redirect('story_list')
    
    context = {
        'story': story,
        'attachments': story.attachments,
        'can_edit': request.user.is_superuser or story.author == request.user,
    }
    return render(request, 'management/story_detail.html', context)



@login_required
def story_list(request):
    """Function-based story list view"""
    queryset = Story.objects.all().select_related('author', 'category')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    author_filter = request.GET.get('author', '')
    category_filter = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    mine_filter = request.GET.get('mine', '')
    
    # Apply filters
    if status_filter and status_filter in ['DRAFT', 'PUBLISHED']:
        queryset = queryset.filter(status=status_filter)
    
    if author_filter:
        queryset = queryset.filter(author__username__icontains=author_filter)
    
    if category_filter:
        queryset = queryset.filter(category__id=category_filter)
    
    if date_from:
        try:
            queryset = queryset.filter(created_at__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            queryset = queryset.filter(created_at__date__lte=date_to)
        except ValueError:
            pass
    
    # Filter by author (my stories)
    if mine_filter == 'true':
        queryset = queryset.filter(author=request.user)
    
    # Order results
    queryset = queryset.order_by('-created_at')
    
    # Get items per page from request, default to 20
    per_page = request.GET.get('per_page', 20)
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 50, 100]:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20
    
    # Get all categories for filter dropdown
    categories = Category.objects.all()
    
    # Pagination
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'page_obj': page_obj,  # For pagination controls
        'stories': page_obj.object_list,  # For the stories loop
        'total_count': Story.objects.count(),
        'published_count': Story.objects.filter(status='PUBLISHED').count(),
        'draft_count': Story.objects.filter(status='DRAFT').count(),
        'categories': categories,
        # Pass filter values back to template
        'current_status': status_filter,
        'current_author': author_filter,
        'current_category': category_filter,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'current_mine': mine_filter,
        'current_per_page': per_page,
    }
    
    return render(request, 'management/story_list.html', context)


# ============================================
# VACANCY VIEWS (Function-based)
# ============================================

@login_required
@permission_required('core.view_vacancy', raise_exception=True)
def vacancy_detail(request, pk):
    """View vacancy details"""
    vacancy = get_object_or_404(
        Vacancy.objects.select_related('author'), 
        pk=pk
    )
    
    context = {
        'vacancy': vacancy,
        'attachments': vacancy.attachments,
        'can_edit': request.user.has_perm('core.change_vacancy'),
    }
    return render(request, 'management/vacancy_detail.html', context)










@login_required
@permission_required('core.change_vacancy', raise_exception=True)
def vacancy_activate(request, pk):
    """Activate a vacancy"""
    vacancy = get_object_or_404(Vacancy, pk=pk)
    vacancy.is_active = True
    vacancy.save()
    messages.success(request, f'Vacancy "{vacancy.title}" activated!')
    return redirect('vacancy_detail', pk=vacancy.pk)


@login_required
@permission_required('core.change_vacancy', raise_exception=True)
def vacancy_deactivate(request, pk):
    """Deactivate a vacancy"""
    vacancy = get_object_or_404(Vacancy, pk=pk)
    vacancy.is_active = False
    vacancy.save()
    messages.success(request, f'Vacancy "{vacancy.title}" deactivated!')
    return redirect('vacancy_detail', pk=vacancy.pk)


@login_required
@permission_required('core.change_vacancy', raise_exception=True)
def vacancy_feature(request, pk):
    """Feature a vacancy"""
    vacancy = get_object_or_404(Vacancy, pk=pk)
    vacancy.is_featured = True
    vacancy.save()
    messages.success(request, f'Vacancy "{vacancy.title}" featured!')
    return redirect('vacancy_detail', pk=vacancy.pk)


@login_required
@permission_required('core.change_vacancy', raise_exception=True)
def vacancy_unfeature(request, pk):
    """Remove feature from a vacancy"""
    vacancy = get_object_or_404(Vacancy, pk=pk)
    vacancy.is_featured = False
    vacancy.save()
    messages.success(request, f'Vacancy "{vacancy.title}" unfeatured!')
    return redirect('vacancy_detail', pk=vacancy.pk)


@login_required
@permission_required('core.delete_vacancy', raise_exception=True)
def vacancy_delete(request, pk):
    """Function-based vacancy delete view"""
    vacancy = get_object_or_404(Vacancy, pk=pk)
    
    if request.method == 'POST':
        vacancy_title = vacancy.title
        vacancy.delete()
        messages.success(request, f'Vacancy "{vacancy_title}" deleted successfully!')
        return redirect('vacancy_list')
    
    # GET request - show confirmation
    context = {
        'object': vacancy,
        'object_type': 'vacancy',
        'object_name': vacancy.title,
        'back_url': reverse_lazy('vacancy_detail', kwargs={'pk': vacancy.pk}),
    }
    return render(request, 'management/confirm_delete.html', context)


@login_required
def vacancy_list(request):
    """Function-based vacancy list view"""
    queryset = Vacancy.objects.all()
    
    # Get all filter parameters
    status = request.GET.get('status', '')
    organization = request.GET.get('organization', '')
    job_type = request.GET.get('job_type', '')
    deadline_from = request.GET.get('deadline_from', '')
    deadline_to = request.GET.get('deadline_to', '')
    featured = request.GET.get('featured', '')
    per_page = request.GET.get('per_page', 20)
    
    # Apply filters
    if status:
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'expired':
            queryset = queryset.filter(expiration_date__lt=timezone.now().date())
    
    if organization:
        queryset = queryset.filter(organization__icontains=organization)
    
    if job_type:
        queryset = queryset.filter(job_type=job_type)
    
    if deadline_from:
        queryset = queryset.filter(application_deadline__gte=deadline_from)
    
    if deadline_to:
        queryset = queryset.filter(application_deadline__lte=deadline_to)
    
    if featured == 'true':
        queryset = queryset.filter(is_featured=True)
    
    # Order results
    queryset = queryset.order_by('-created_at')
    
    # Calculate expired count
    expired_count = Vacancy.objects.filter(
        Q(expiration_date__lt=timezone.now().date()) | 
        Q(application_deadline__lt=timezone.now().date())
    ).count()
    
    # Pagination
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 50, 100]:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20
    
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'vacancies': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': Vacancy.objects.count(),
        'active_count': Vacancy.objects.filter(is_active=True).count(),
        'expired_count': expired_count,
        'featured_count': Vacancy.objects.filter(is_featured=True).count(),
        'now': timezone.now(),  # Add current time
        # Filter parameters for template
        'current_status': status,
        'current_organization': organization,
        'current_job_type': job_type,
        'current_deadline_from': deadline_from,
        'current_deadline_to': deadline_to,
        'current_featured': featured,
        'current_per_page': per_page,
    }
    
    return render(request, 'management/vacancy_list.html', context)


# ============================================
# NOTICE VIEWS (Function-based)
# ============================================

@login_required
@permission_required('core.view_notice', raise_exception=True)
def notice_detail(request, pk):
    """View notice details"""
    notice = get_object_or_404(
        Notice.objects.select_related('author'), 
        pk=pk
    )
    
    context = {
        'notice': notice,
        'attachments': notice.attachments,
        'can_edit': request.user.has_perm('core.change_notice'),
    }
    return render(request, 'management/notice_detail.html', context)







@login_required
@permission_required('core.delete_notice', raise_exception=True)
def notice_delete(request, pk):
    """Function-based notice delete view"""
    notice = get_object_or_404(Notice, pk=pk)
    
    if request.method == 'POST':
        notice_headline = notice.headline
        notice.delete()
        messages.success(request, f'Notice "{notice_headline}" deleted successfully!')
        return redirect('notice_list')
    
    # GET request - show confirmation
    context = {
        'object': notice,
        'object_type': 'notice',
        'object_name': notice.headline,
        'back_url': reverse_lazy('notice_detail', kwargs={'pk': notice.pk}),
    }
    return render(request, 'management/confirm_delete.html', context)


@login_required
def notice_list(request):
    """Function-based notice list view"""
    queryset = Notice.objects.all()
    
    # Get all filter parameters
    status = request.GET.get('status', '')
    organization = request.GET.get('organization', '')
    category = request.GET.get('category', '')
    publish_from = request.GET.get('publish_from', '')
    publish_to = request.GET.get('publish_to', '')
    important = request.GET.get('important', '')
    per_page = request.GET.get('per_page', 20)
    
    # Apply filters
    if status:
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'expired':
            queryset = queryset.filter(expiration_date__lt=timezone.now().date())
    
    if organization:
        queryset = queryset.filter(organization__icontains=organization)
    
    if category in ['EVENT', 'TENDER', 'ANNOUNCEMENT']:
        queryset = queryset.filter(category=category)
    
    if publish_from:
        queryset = queryset.filter(publish_date__gte=publish_from)
    
    if publish_to:
        queryset = queryset.filter(publish_date__lte=publish_to)
    
    if important == 'true':
        queryset = queryset.filter(is_important=True)
    
    # Order results
    queryset = queryset.order_by('-publish_date', '-created_at')
    
    # Calculate important count
    important_count = Notice.objects.filter(is_important=True).count()
    
    # Calculate attachment count
    from django.contrib.contenttypes.models import ContentType
    notice_content_type = ContentType.objects.get_for_model(Notice)
    attachment_count = GenericAttachment.objects.filter(
        content_type=notice_content_type
    ).count()
    
    # Pagination
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 50, 100]:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20
    
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'notices': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': Notice.objects.count(),
        'active_count': Notice.objects.filter(is_active=True).count(),
        'important_count': important_count,
        'attachment_count': attachment_count,
        'now': timezone.now(),  # Add current time
        # Filter parameters for template
        'current_status': status,
        'current_organization': organization,
        'current_category': category,
        'current_publish_from': publish_from,
        'current_publish_to': publish_to,
        'current_important': important,
        'current_per_page': per_page,
    }
    
    return render(request, 'management/notice_list.html', context)


@login_required
@permission_required('core.change_notice', raise_exception=True)
def notice_activate(request, pk):
    """Activate a notice"""
    notice = get_object_or_404(Notice, pk=pk)
    notice.is_active = True
    notice.save()
    messages.success(request, f'Notice "{notice.headline}" activated!')
    return redirect('notice_detail', pk=notice.pk)


@login_required
@permission_required('core.change_notice', raise_exception=True)
def notice_deactivate(request, pk):
    """Deactivate a notice"""
    notice = get_object_or_404(Notice, pk=pk)
    notice.is_active = False
    notice.save()
    messages.success(request, f'Notice "{notice.headline}" deactivated!')
    return redirect('notice_detail', pk=notice.pk)


@login_required
@permission_required('core.change_notice', raise_exception=True)
def notice_mark_important(request, pk):
    """Mark a notice as important"""
    notice = get_object_or_404(Notice, pk=pk)
    notice.is_important = True
    notice.save()
    messages.success(request, f'Notice "{notice.headline}" marked as important!')
    return redirect('notice_detail', pk=notice.pk)


@login_required
@permission_required('core.change_notice', raise_exception=True)
def notice_unmark_important(request, pk):
    """Remove important mark from a notice"""
    notice = get_object_or_404(Notice, pk=pk)
    notice.is_important = False
    notice.save()
    messages.success(request, f'Notice "{notice.headline}" removed from important!')
    return redirect('notice_detail', pk=notice.pk)


# ============================================
# CATEGORY VIEWS (Function-based)
# ============================================





@login_required
@permission_required('core.delete_category', raise_exception=True)
def category_delete(request, pk):
    """Function-based view for deleting categories"""
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


@login_required
def category_list(request):
    """Function-based category list view"""
    categories = Category.objects.annotate(
        story_count=Count('story')
    ).order_by('name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'management/category_list.html', context)


# ============================================
# ATTACHMENT VIEWS
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
# DASHBOARD/OVERVIEW VIEWS
# ============================================

from datetime import timedelta

@login_required
def dashboard(request):
    """User dashboard showing their content"""
    
    # Get date ranges
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    last_month_end = start_of_month - timedelta(days=1)
    
    # Story statistics
    total_stories = Story.objects.count()
    
    # Stories from this month
    stories_this_month = Story.objects.filter(
        created_at__date__gte=start_of_month
    ).count()
    
    # Stories from last month
    stories_last_month = Story.objects.filter(
        created_at__date__gte=last_month_start,
        created_at__date__lte=last_month_end
    ).count()
    
    # Calculate new stories (this month vs last month)
    new_stories = stories_this_month - stories_last_month
    if new_stories > 0:
        new_stories = f"+{new_stories}"
    else:
        new_stories = str(new_stories)
    
    # Published stories
    stories_published = Story.objects.filter(status='PUBLISHED').count()
    
    # Calculate publishing rate
    publishing_rate = 0
    if total_stories > 0:
        publishing_rate = round((stories_published / total_stories) * 100)
    
    # Pending stories (drafts)
    pending = Story.objects.filter(status='DRAFT').count()
    
    # If you have a Subscriber model
    try:
        from accounts.models import Subscriber  # Adjust import as needed
        subscribers = Subscriber.objects.filter(is_active=True).count()
        
        # New subscribers this month
        new_subscribers_this_month = Subscriber.objects.filter(
            subscribed_at__date__gte=start_of_month,
            is_active=True
        ).count()
        
        new_subscribers = f"+{new_subscribers_this_month}"
        
    except (ImportError, AttributeError):
        # Fallback if Subscriber model doesn't exist
        subscribers = 0
        new_subscribers = "+0"
    
    # User-specific content
    user_stories = Story.objects.filter(author=request.user).order_by('-created_at')[:5]
    recent_vacancies = Vacancy.objects.filter(is_active=True).order_by('-created_at')[:5]
    recent_notices = Notice.objects.filter(is_active=True).order_by('-created_at')[:5]
    categories = Category.objects.all()[:10]
    
    context = {
        # Dashboard stats
        'total_stories': total_stories,
        'new_stories': new_stories,
        'stories_published': stories_published,
        'publishing_rate': publishing_rate,
        'pending': pending,
        'subscribers': subscribers,
        'new_subscribers': new_subscribers,
        
        # User content
        'user_stories': user_stories,
        'recent_vacancies': recent_vacancies,
        'recent_notices': recent_notices,
        'categories': categories,
        
        # Date info
        'today': today.strftime("%B %d, %Y"),
        'current_month': today.strftime("%B %Y"),
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