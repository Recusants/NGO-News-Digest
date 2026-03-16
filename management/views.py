# views.py - COMPLETE FILE (FUNCTION-BASED VIEWS ONLY)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
import json
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.utils.html import strip_tags
from django.utils import timezone
from datetime import datetime

from django.db.models import Q
from publisher.models import Story, Vacancy, Notice, Category, GenericAttachment
from publisher.forms import StoryForm, VacancyForm, NoticeForm, CategoryForm
from publisher.utils.attachment_utils import attach_multiple_files_to_object
from publisher.views import notify_subscribers

from accounts.models import User

from django.http import Http404


from django.views.decorators.http import require_POST






# views.py - UPDATED FUNCTIONS ONLY

# ============================================
# VACANCY VIEWS (Function-based)
# ============================================

# ============================================
# VACANCY VIEWS (Function-based) - AJAX ready
# ============================================


@login_required
def vacancy_edit(request, pk):
    """Edit an existing vacancy"""
    try:
        vacancy = get_object_or_404(Vacancy, id=pk)
        
        # Check if user is author OR has 'Publisher' in roles
        is_author = vacancy.author == request.user
        is_publisher = hasattr(request.user, 'roles') and 'Publisher' in request.user.roles
        
        if not (is_author or is_publisher):
            # For AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'icon': 'error',
                    'title': 'Permission Denied',
                    'message': f'You do not have permission. Ony a publisher or {vacancy.author.first_name.title()} {vacancy.author.last_name.title()} can edit this vacancy'
                }, status=403)
            
            # For regular GET requests (clicking edit link)
            messages.error(request, f'You do not have permission. Ony a publisher or {vacancy.author.first_name.title()} {vacancy.author.last_name.title()} can edit this vacancy')
            
            # Redirect back to the referring page or list
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('vacancy_list')
        
        if request.method == "POST":
            try:
                # Get data from POST request
                title = request.POST.get('title')
                organization = request.POST.get('organization')
                organization_details = request.POST.get('organization_details')
                description = request.POST.get('description')
                how_to_apply = request.POST.get('how_to_apply')
                location = request.POST.get('location')
                job_type = request.POST.get('job_type')
                application_deadline = request.POST.get('application_deadline')
                application_link = request.POST.get('application_link', '')
                is_active = request.POST.get('is_active') == 'true'
                is_featured = request.POST.get('is_featured') == 'true'
                expiration_date = request.POST.get('expiration_date')
                
                # Validation
                errors = {}
                
                if not title:
                    errors['title'] = ['Title is required']
                elif len(title) > 200:
                    errors['title'] = ['Title cannot exceed 200 characters']
                    
                if not organization:
                    errors['organization'] = ['Organization is required']
                elif len(organization) > 200:
                    errors['organization'] = ['Organization cannot exceed 200 characters']
                    
                if not organization_details:
                    errors['organization_details'] = ['Organization details are required']
                elif len(organization_details) > 200:
                    errors['organization_details'] = ['Organization details cannot exceed 200 characters']
                    
                if not description or description == '<p><br></p>' or description == '<br>':
                    errors['description'] = ['Description cannot be blank']
                    
                if not how_to_apply or how_to_apply == '<p><br></p>' or how_to_apply == '<br>':
                    errors['how_to_apply'] = ['How to apply cannot be blank']
                    
                if not location:
                    errors['location'] = ['Location is required']
                    
                if not job_type:
                    errors['job_type'] = ['Job type is required']
                elif job_type not in ['FULL_TIME', 'PART_TIME', 'CONTRACT']:
                    errors['job_type'] = ['Invalid job type']
                    
                if not application_deadline:
                    errors['application_deadline'] = ['Application deadline is required']
                
                if errors:
                    return JsonResponse({
                        'icon': 'error',
                        'title': 'Validation Error',
                        'message': 'Please correct the errors in the form',
                        'errors': errors
                    }, status=400)
                
                # Update vacancy fields
                vacancy.title = title
                vacancy.organization = organization
                vacancy.organization_details = organization_details
                vacancy.description = description
                vacancy.how_to_apply = how_to_apply
                vacancy.location = location
                vacancy.job_type = job_type
                vacancy.application_deadline = application_deadline
                vacancy.application_link = application_link
                vacancy.is_active = is_active
                vacancy.is_featured = is_featured
                vacancy.expiration_date = expiration_date if expiration_date else None
                vacancy.save()
                
                # Handle new attachments
                content_type = ContentType.objects.get_for_model(Vacancy)
                existing_count = vacancy.attachments.count()
                
                for key, file in request.FILES.items():
                    if key.startswith('attachment_'):
                        GenericAttachment.objects.create(
                            content_type=content_type,
                            object_id=vacancy.id,
                            file=file,
                            order=existing_count
                        )
                        existing_count += 1
                
                # Handle deleted attachments (if any)
                deleted_attachments = request.POST.get('deleted_attachments', '')
                if deleted_attachments:
                    for att_id in deleted_attachments.split(','):
                        if att_id.strip():
                            try:
                                att = GenericAttachment.objects.get(id=att_id.strip())
                                if att.content_object == vacancy:
                                    if att.file:
                                        att.file.delete()
                                    att.delete()
                            except GenericAttachment.DoesNotExist:
                                pass
                
                return JsonResponse({
                    'icon': 'success',
                    'title': 'Success!',
                    'message': 'Vacancy updated successfully',
                    'vacancy_id': vacancy.id,
                    'redirect_url': reverse('vacancy_page', args=[vacancy.id])
                }, status=200)
                
            except Exception as e:
                print(f"Error updating vacancy: {str(e)}")
                return JsonResponse({
                    'icon': 'error',
                    'title': 'Server Error',
                    'message': 'An error occurred while updating the vacancy.'
                }, status=500)
        
        # GET request - render edit form
        else:
            # Get existing attachments
            attachments = vacancy.attachments.all()
            
            context = {
                'vacancy': vacancy,
                'attachments': attachments,
                'job_types': Vacancy.JOB_TYPES,
                'is_edit': True,
            }
            return render(request, 'management/vacancy/edit_vacancy.html', context)
            
    except Vacancy.DoesNotExist:
        messages.error(request, 'Vacancy not found')
        return redirect('vacancy_list')


@login_required
@permission_required('core.add_vacancy', raise_exception=True)
def vacancy_create(request):
    """Create a new vacancy with AJAX support"""
    if request.method == "POST":
        try:
            # Get data from POST request
            title = request.POST.get('title')
            organization = request.POST.get('organization')
            organization_details = request.POST.get('organization_details')
            description = request.POST.get('description')
            how_to_apply = request.POST.get('how_to_apply')
            location = request.POST.get('location')
            job_type = request.POST.get('job_type')
            application_deadline = request.POST.get('application_deadline')
            application_link = request.POST.get('application_link', '')
            is_active = request.POST.get('is_active') == 'true'
            is_featured = request.POST.get('is_featured') == 'true'
            expiration_date = request.POST.get('expiration_date')
            
            # Validation
            errors = {}
            
            if not title:
                errors['title'] = ['Title is required']
            elif len(title) > 200:
                errors['title'] = ['Title cannot exceed 200 characters']
                
            if not organization:
                errors['organization'] = ['Organization is required']
            elif len(organization) > 200:
                errors['organization'] = ['Organization cannot exceed 200 characters']
                
            if not organization_details:
                errors['organization_details'] = ['Organization details are required']
            elif len(organization_details) > 200:
                errors['organization_details'] = ['Organization details cannot exceed 200 characters']
                
            if not description or description == '<p><br></p>' or description == '<br>':
                errors['description'] = ['Description cannot be blank']
                
            if not how_to_apply or how_to_apply == '<p><br></p>' or how_to_apply == '<br>':
                errors['how_to_apply'] = ['How to apply cannot be blank']
                
            if not location:
                errors['location'] = ['Location is required']
                
            if not job_type:
                errors['job_type'] = ['Job type is required']
            elif job_type not in ['FULL_TIME', 'PART_TIME', 'CONTRACT']:
                errors['job_type'] = ['Invalid job type']
                
            if not application_deadline:
                errors['application_deadline'] = ['Application deadline is required']
            
            # Return validation errors if any
            if errors:
                return JsonResponse({
                    'icon': 'error',
                    'title': 'Validation Error',
                    'message': 'Please correct the errors in the form',
                    'errors': errors
                }, status=400)
            
            # Create the vacancy
            vacancy = Vacancy.objects.create(
                title=title,
                organization=organization,
                organization_details=organization_details,
                description=description,
                how_to_apply=how_to_apply,
                location=location,
                job_type=job_type,
                application_deadline=application_deadline,
                application_link=application_link,
                is_active=is_active,
                is_featured=is_featured,
                expiration_date=expiration_date if expiration_date else None,
                author=request.user
            )
            
            # Handle file attachments
            attachments = []
            for key, file in request.FILES.items():
                if key.startswith('attachment_'):
                    attachments.append(file)
            
            # Save attachments
            content_type = ContentType.objects.get_for_model(Vacancy)
            for index, file in enumerate(attachments):
                attachment = GenericAttachment.objects.create(
                    content_type=content_type,
                    object_id=vacancy.id,
                    file=file,
                    order=index
                )
            
            # Return success response
            return JsonResponse({
                'icon': 'success',
                'title': 'Success!',
                'message': f'Vacancy created successfully with {len(attachments)} attachment(s)',
                'vacancy_id': vacancy.id,
                'redirect_url': reverse('vacancy_list')
            }, status=201)
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error creating vacancy: {str(e)}")
            return JsonResponse({
                'icon': 'error',
                'title': 'Server Error',
                'message': 'An error occurred while creating the vacancy. Please try again.'
            }, status=500)
    
    # GET request - render the form
    else:
        context = {
            'job_types': Vacancy.JOB_TYPES,
        }
        return render(request, 'management/vacancy/create_vacancy.html', context)




# ============================================
# NOTICE VIEWS (Function-based)
# ============================================
@login_required
@require_POST
def notice_toggle_important(request, pk):
    """Toggle notice important status"""
    try:
        notice = get_object_or_404(Notice, id=pk)
        
        # Check if user is author OR has 'Publisher' in roles
        is_author = notice.author == request.user
        is_publisher = hasattr(request.user, 'roles') and 'Publisher' in request.user.roles
        
        if not (is_author or is_publisher):
            return JsonResponse({
                'icon': 'error',
                'title': 'Permission Denied',
                'message': 'You do not have permission to modify this notice'
            }, status=403)
        
        notice.is_important = not notice.is_important
        notice.save()
        
        return JsonResponse({
            'icon': 'success',
            'title': 'Success!',
            'message': f'Notice marked as {"important" if notice.is_important else "not important"}',
            'is_important': notice.is_important
        })
        
    except Notice.DoesNotExist:
        return JsonResponse({
            'icon': 'error',
            'title': 'Error',
            'message': 'Notice not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'icon': 'error',
            'title': 'Server Error',
            'message': 'An error occurred. Please try again.'
        }, status=500)


@login_required
@require_POST
def notice_toggle_active(request, pk):
    """Toggle notice active status"""
    try:
        notice = get_object_or_404(Notice, id=pk)
        
        # Check if user is author OR has 'Publisher' in roles
        is_author = notice.author == request.user
        is_publisher = hasattr(request.user, 'roles') and 'Publisher' in request.user.roles
        
        if not (is_author or is_publisher):
            return JsonResponse({
                'icon': 'error',
                'title': 'Permission Denied',
                'message': 'You do not have permission to modify this notice'
            }, status=403)
        
        notice.is_active = not notice.is_active
        notice.save()
        
        return JsonResponse({
            'icon': 'success',
            'title': 'Success!',
            'message': f'Notice marked as {"active" if notice.is_active else "inactive"}',
            'is_active': notice.is_active
        })
        
    except Notice.DoesNotExist:
        return JsonResponse({
            'icon': 'error',
            'title': 'Error',
            'message': 'Notice not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'icon': 'error',
            'title': 'Server Error',
            'message': 'An error occurred. Please try again.'
        }, status=500)


@login_required
def notice_create(request):
    """Create a new notice with AJAX support"""
    if request.method == "POST":
        try:
            # Get data from POST request
            headline = request.POST.get('headline')
            overview = request.POST.get('overview')
            description = request.POST.get('description')
            contact_details = request.POST.get('contact_details')
            organization = request.POST.get('organization')
            category = request.POST.get('category')
            publish_date = request.POST.get('publish_date')
            expiration_date = request.POST.get('expiration_date')
            is_active = request.POST.get('is_active') == 'true'
            is_important = request.POST.get('is_important') == 'true'
            
            # Validation
            errors = {}
            
            if not headline:
                errors['headline'] = ['Headline is required']
            elif len(headline) > 200:
                errors['headline'] = ['Headline cannot exceed 200 characters']
                
            if not overview:
                errors['overview'] = ['Overview is required']
            elif len(overview) > 500:
                errors['overview'] = ['Overview cannot exceed 500 characters']
                
            if not description or description == '<p><br></p>' or description == '<br>':
                errors['description'] = ['Description cannot be blank']
                
            if not contact_details or contact_details == '<p><br></p>' or contact_details == '<br>':
                errors['contact_details'] = ['Contact details cannot be blank']
                
            if not organization:
                errors['organization'] = ['Organization is required']
            elif len(organization) > 200:
                errors['organization'] = ['Organization cannot exceed 200 characters']
                
            if not category:
                errors['category'] = ['Category is required']
            elif category not in ['EVENT', 'TENDER', 'ANNOUNCEMENT']:
                errors['category'] = ['Invalid category']
            
            # Return validation errors if any
            if errors:
                return JsonResponse({
                    'icon': 'error',
                    'title': 'Validation Error',
                    'message': 'Please correct the errors in the form',
                    'errors': errors
                }, status=400)
            
            # Create the notice
            notice = Notice.objects.create(
                headline=headline,
                overview=overview,
                description=description,
                contact_details=contact_details,
                organization=organization,
                category=category,
                publish_date=publish_date if publish_date else timezone.now().date(),
                expiration_date=expiration_date if expiration_date else None,
                is_active=is_active,
                is_important=is_important,
                author=request.user
            )
            
            # Handle file attachments
            attachments = []
            for key, file in request.FILES.items():
                if key.startswith('attachment_'):
                    attachments.append(file)
            
            # Save attachments
            content_type = ContentType.objects.get_for_model(Notice)
            for index, file in enumerate(attachments):
                attachment = GenericAttachment.objects.create(
                    content_type=content_type,
                    object_id=notice.id,
                    file=file,
                    order=index
                )
            
            # Return success response
            return JsonResponse({
                'icon': 'success',
                'title': 'Success!',
                'message': f'Notice created successfully with {len(attachments)} attachment(s)',
                'notice_id': notice.id,
                'redirect_url': reverse('notice_list')
            }, status=201)
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error creating notice: {str(e)}")
            return JsonResponse({
                'icon': 'error',
                'title': 'Server Error',
                'message': 'An error occurred while creating the notice. Please try again.'
            }, status=500)
    
    # GET request - render the form
    else:
        context = {
            'categories': Notice.CATEGORIES,
        }
        return render(request, 'management/notice/create_notice.html', context)


@login_required
def notice_edit(request, pk):
    """Edit an existing notice"""
    try:
        notice = get_object_or_404(Notice, id=pk)
        
        # Check if user is author OR has 'Publisher' in roles
        is_author = notice.author == request.user
        is_publisher = hasattr(request.user, 'roles') and 'Publisher' in request.user.roles
        
        if not (is_author or is_publisher):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'icon': 'error',
                    'title': 'Permission Denied',
                    'message': 'You do not have permission to edit this notice'
                }, status=403)
            else:
                messages.error(request, 'You do not have permission to edit this notice')
                return redirect('notice_list')
        
        if request.method == "POST":
            try:
                # Get data from POST request
                headline = request.POST.get('headline')
                overview = request.POST.get('overview')
                description = request.POST.get('description')
                contact_details = request.POST.get('contact_details')
                organization = request.POST.get('organization')
                category = request.POST.get('category')
                publish_date = request.POST.get('publish_date')
                expiration_date = request.POST.get('expiration_date')
                is_active = request.POST.get('is_active') == 'true'
                is_important = request.POST.get('is_important') == 'true'
                
                # Validation
                errors = {}
                
                if not headline:
                    errors['headline'] = ['Headline is required']
                elif len(headline) > 200:
                    errors['headline'] = ['Headline cannot exceed 200 characters']
                    
                if not overview:
                    errors['overview'] = ['Overview is required']
                elif len(overview) > 500:
                    errors['overview'] = ['Overview cannot exceed 500 characters']
                    
                if not description or description == '<p><br></p>' or description == '<br>':
                    errors['description'] = ['Description cannot be blank']
                    
                if not contact_details or contact_details == '<p><br></p>' or contact_details == '<br>':
                    errors['contact_details'] = ['Contact details cannot be blank']
                    
                if not organization:
                    errors['organization'] = ['Organization is required']
                elif len(organization) > 200:
                    errors['organization'] = ['Organization cannot exceed 200 characters']
                    
                if not category:
                    errors['category'] = ['Category is required']
                elif category not in ['EVENT', 'TENDER', 'ANNOUNCEMENT']:
                    errors['category'] = ['Invalid category']
                
                if errors:
                    return JsonResponse({
                        'icon': 'error',
                        'title': 'Validation Error',
                        'message': 'Please correct the errors in the form',
                        'errors': errors
                    }, status=400)
                
                # Update notice fields
                notice.headline = headline
                notice.overview = overview
                notice.description = description
                notice.contact_details = contact_details
                notice.organization = organization
                notice.category = category
                notice.publish_date = publish_date if publish_date else timezone.now().date()
                notice.expiration_date = expiration_date if expiration_date else None
                notice.is_active = is_active
                notice.is_important = is_important
                notice.save()
                
                # Handle new attachments
                content_type = ContentType.objects.get_for_model(Notice)
                existing_count = notice.attachments.count()
                
                for key, file in request.FILES.items():
                    if key.startswith('attachment_'):
                        GenericAttachment.objects.create(
                            content_type=content_type,
                            object_id=notice.id,
                            file=file,
                            order=existing_count
                        )
                        existing_count += 1
                
                # Handle deleted attachments (if any)
                deleted_attachments = request.POST.get('deleted_attachments', '')
                if deleted_attachments:
                    for att_id in deleted_attachments.split(','):
                        if att_id.strip():
                            try:
                                att = GenericAttachment.objects.get(id=att_id.strip())
                                if att.content_object == notice:
                                    if att.file:
                                        att.file.delete()
                                    att.delete()
                            except GenericAttachment.DoesNotExist:
                                pass
                
                return JsonResponse({
                    'icon': 'success',
                    'title': 'Success!',
                    'message': 'Notice updated successfully',
                    'notice_id': notice.id,
                    'redirect_url': reverse('notice_page', args=[notice.id])
                }, status=200)
                
            except Exception as e:
                print(f"Error updating notice: {str(e)}")
                return JsonResponse({
                    'icon': 'error',
                    'title': 'Server Error',
                    'message': 'An error occurred while updating the notice.'
                }, status=500)
        
        # GET request - render edit form
        else:
            # Get existing attachments
            attachments = notice.attachments.all()
            
            context = {
                'notice': notice,
                'attachments': attachments,
                'categories': Notice.CATEGORIES,
                'is_edit': True,
            }
            return render(request, 'management/notice/edit.html', context)
            
    except Notice.DoesNotExist:
        messages.error(request, 'Notice not found')
        return redirect('notice_list')


# ============================================
# STORY VIEWS (Function-based)
# ============================================


@login_required
def story_publish(request, pk):
    """Publish a story and notify subscribers"""
    try:
        story = get_object_or_404(Story, id=pk, author=request.user)
        
        if story.status == 'DRAFT':
            story.status = 'PUBLISHED'
            story.published_at = timezone.now()
            story.save()
            
            # Notify subscribers in background thread
            notify_subscribers(story.id)
            
            return JsonResponse({
                'icon': 'success',
                'title': 'Success!',
                'message': 'Story published successfully. Subscribers will be notified.',
                'status': 'PUBLISHED'
            })
        else:
            return JsonResponse({
                'icon': 'info',
                'title': 'Already Published',
                'message': 'This story is already published',
                'status': story.status
            })
            
    except Http404:
        return JsonResponse({
            'icon': 'error',
            'title': 'Not Found',
            'message': 'Story not found or you do not have permission'
        }, status=404)
    except Exception as e:
        # Log the error for debugging
        print(f"Error in story_publish: {str(e)}")
        return JsonResponse({
            'icon': 'error',
            'title': 'Server Error',
            'message': 'An error occurred. Please try again.'
        }, status=500)



@login_required
@require_POST
def story_unpublish(request, pk):
    """Unpublish a story (revert to draft)"""
    try:
        story = get_object_or_404(Story, id=pk, author=request.user)
        
        if story.status == 'PUBLISHED':
            story.status = 'DRAFT'
            story.published_at = None
            story.save()
            
            return JsonResponse({
                'icon': 'success',
                'title': 'Success!',
                'message': 'Story unpublished and reverted to draft',
                'status': 'DRAFT'
            })
        else:
            return JsonResponse({
                'icon': 'info',
                'title': 'Already Draft',
                'message': 'This story is already in draft mode',
                'status': story.status
            })
            
    except Story.DoesNotExist:
        return JsonResponse({
            'icon': 'error',
            'title': 'Error',
            'message': 'Story not found or you do not have permission'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'icon': 'error',
            'title': 'Server Error',
            'message': 'An error occurred. Please try again.'
        }, status=500)


@login_required
def story_create(request):
    if request.method == "POST":
        try:
            # Get data from POST request
            headline = request.POST.get('headline')
            snippet = request.POST.get('snippet')
            content = request.POST.get('content')
            read_time = request.POST.get('read_time')
            category_id = request.POST.get('category')
            
            # Validation
            errors = {}
            
            if not headline:
                errors['headline'] = ['Headline is required']
            elif len(headline) > 200:
                errors['headline'] = ['Headline cannot exceed 200 characters']
                
            if not snippet:
                errors['snippet'] = ['Snippet is required']
            elif len(snippet) > 500:
                errors['snippet'] = ['Snippet cannot exceed 500 characters']
                
            if not content or content == '<p><br></p>' or content == '<br>':
                errors['content'] = ['Content cannot be blank']
                
            if not read_time:
                errors['read_time'] = ['Read time is required']
            elif len(read_time) > 20:
                errors['read_time'] = ['Read time cannot exceed 20 characters']
            
            # Return validation errors if any
            if errors:
                return JsonResponse({
                    'icon': 'error',
                    'title': 'Validation Error',
                    'message': 'Please correct the errors in the form',
                    'errors': errors
                }, status=400)
            
            # Handle category (convert '0' to None)
            category = None
            if category_id and category_id != '0':
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    return JsonResponse({
                        'icon': 'error',
                        'title': 'Category Error',
                        'message': 'Invalid category selected'
                    }, status=400)
            
            # Handle thumbnail upload
            thumbnail = request.FILES.get('thumbnail')
            
            # Create the story with DRAFT status by default
            story = Story.objects.create(
                headline=headline,
                snippet=snippet,
                content=content,
                read_time=read_time,
                status='DRAFT',  # Always save as DRAFT
                author=request.user,
                category=category,
                thumbnail=thumbnail
            )
            
            # Return success response with icon, title, and message
            return JsonResponse({
                'icon': 'success',
                'title': 'Success!',
                'message': 'Story saved as draft successfully',
                'story_id': story.id,
                'redirect_url': reverse('story_page', args=[story.id])
            }, status=201)
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error creating story: {str(e)}")
            return JsonResponse({
                'icon': 'error',
                'title': 'Server Error',
                'message': 'An error occurred while creating the story. Please try again.'
            }, status=500)
    
    # GET request - render the form
    else:
        categories = Category.objects.all()
        context = {
            'categories': categories,
        }
        return render(request, 'management/story/create_story.html', context)





# ============================================
# CATEGORY VIEWS (Function-based)
# ============================================


@login_required
def category_create_ajax(request):
    if request.method == 'POST':
        name = request.POST.get('name').lower().strip()
        
        if not name:
            return JsonResponse({'success': False, 'message': 'Category name is required'})
        
        # Check if category already exists
        category, created = Category.objects.get_or_create(
            name__iexact=name,
            defaults={'name': name}
        )
        
        return JsonResponse({
            'success': True,
            'category_id': category.id,
            'created': created,
            'message': 'Category created successfully' if created else 'Category already exists'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

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
def story_edit(request, pk):
    story = get_object_or_404(Story, id=pk, author=request.user)
    
    if request.method == "POST":
        try:
            # Get data from POST request
            headline = request.POST.get('headline')
            snippet = request.POST.get('snippet')
            content = request.POST.get('content')
            read_time = request.POST.get('read_time')
            category_id = request.POST.get('category')
            remove_thumbnail = request.POST.get('remove_thumbnail') == '1'
            
            # Validation
            errors = {}
            
            if not headline:
                errors['headline'] = ['Headline is required']
            elif len(headline) > 200:
                errors['headline'] = ['Headline cannot exceed 200 characters']
                
            if not snippet:
                errors['snippet'] = ['Snippet is required']
            elif len(snippet) > 500:
                errors['snippet'] = ['Snippet cannot exceed 500 characters']
                
            if not content or content == '<p><br></p>' or content == '<br>':
                errors['content'] = ['Content cannot be blank']
                
            if not read_time:
                errors['read_time'] = ['Read time is required']
            elif len(read_time) > 20:
                errors['read_time'] = ['Read time cannot exceed 20 characters']
            
            if errors:
                return JsonResponse({
                    'icon': 'error',
                    'title': 'Validation Error',
                    'message': 'Please correct the errors in the form',
                    'errors': errors
                }, status=400)
            
            # Handle category
            category = None
            if category_id and category_id != '0':
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    return JsonResponse({
                        'icon': 'error',
                        'title': 'Category Error',
                        'message': 'Invalid category selected'
                    }, status=400)
            
            # Update story fields
            story.headline = headline
            story.snippet = snippet
            story.content = content
            story.read_time = read_time
            story.category = category
            
            # Handle thumbnail
            thumbnail = request.FILES.get('thumbnail')
            if thumbnail:
                story.thumbnail = thumbnail
            elif remove_thumbnail:
                story.thumbnail = None
            
            story.save()
            
            return JsonResponse({
                'icon': 'success',
                'title': 'Success!',
                'message': 'Story updated successfully',
                'story_id': story.id,
                'redirect_url': reverse('story_page', args=[story.id])
            }, status=200)
            
        except Exception as e:
            print(f"Error updating story: {str(e)}")
            return JsonResponse({
                'icon': 'error',
                'title': 'Server Error',
                'message': 'An error occurred while updating the story. Please try again.'
            }, status=500)
    
    # GET request - render the form
    else:
        categories = Category.objects.all()
        context = {
            'story': story,
            'categories': categories,
        }
        return render(request, 'management/story/edit_story.html', context)




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
    """Enhanced story list view with better filters and pagination"""
    
    # Base queryset with optimization
    queryset = Story.objects.select_related('author', 'category').order_by('-created_at')
    
    # Get filter parameters
    filters = {
        'status': request.GET.get('status', ''),
        'author': request.GET.get('author', ''),
        'category': request.GET.get('category', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
        'mine': request.GET.get('mine', ''),
        'search': request.GET.get('search', ''),  # Added search
    }
    
    # Store active filters count for UI
    active_filters = {k: v for k, v in filters.items() if v and k != 'search'}
    
    # Apply filters
    if filters['status'] in ['DRAFT', 'PUBLISHED']:
        queryset = queryset.filter(status=filters['status'])
    
    if filters['author']:
        queryset = queryset.filter(
            Q(author__username__icontains=filters['author']) |
            Q(author__first_name__icontains=filters['author']) |
            Q(author__last_name__icontains=filters['author'])
        )
    
    if filters['category'] and filters['category'].isdigit():
        queryset = queryset.filter(category__id=filters['category'])
    
    # Search in headline and content
    if filters['search']:
        queryset = queryset.filter(
            Q(headline__icontains=filters['search']) |
            Q(snippet__icontains=filters['search']) |
            Q(content__icontains=filters['search'])
        )
    
    # Date range filters
    if filters['date_from']:
        try:
            date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=date_from)
        except (ValueError, TypeError):
            pass
    
    if filters['date_to']:
        try:
            date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=date_to)
        except (ValueError, TypeError):
            pass
    
    # My stories filter
    if filters['mine'] == 'true':
        queryset = queryset.filter(author=request.user)
    
    # Pagination with improved options
    per_page_options = [10, 20, 50, 100, 250]
    per_page = request.GET.get('per_page', 20)
    try:
        per_page = int(per_page)
        if per_page not in per_page_options:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20
    
    # Get page number
    page_number = request.GET.get('page', 1)
    
    # Create paginator
    paginator = Paginator(queryset, per_page)
    paginator.elided_page_range = paginator.get_elided_page_range(
        number=page_number, 
        on_each_side=2, 
        on_ends=1
    )
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get categories for filter dropdown with count
    categories = Category.objects.annotate(
        story_count=Count('story')
    ).filter(story_count__gt=0).order_by('name')
    
    # Get authors with stories for filter dropdown
    authors = User.objects.filter(
        story__isnull=False
    ).distinct().annotate(
        story_count=Count('story')
    ).order_by('username')
    
    # Get counts for stats cards
    total_count = Story.objects.count()
    published_count = Story.objects.filter(status='PUBLISHED').count()
    draft_count = Story.objects.filter(status='DRAFT').count()
    
    # Get counts for current filtered queryset
    filtered_count = queryset.count()
    
    # Build pagination URL with all current filters
    pagination_url = '?' + '&'.join([
        f'{k}={v}' for k, v in filters.items() 
        if v and k != 'page'
    ])
    if pagination_url == '?':
        pagination_url = '?'
    else:
        pagination_url += '&'
    
    context = {
        # Pagination
        'page_obj': page_obj,
        'stories': page_obj.object_list,
        'paginator': paginator,
        'pagination_url': pagination_url,
        
        # Statistics
        'total_count': total_count,
        'published_count': published_count,
        'draft_count': draft_count,
        'filtered_count': filtered_count,
        'active_filter_count': len(active_filters),
        
        # Filter data
        'categories': categories,
        'authors': authors,
        'current_filters': filters,
        'current_per_page': per_page,
        'per_page_options': per_page_options,
        
        # Preserve filter values in template
        'current_status': filters['status'],
        'current_author': filters['author'],
        'current_category': filters['category'],
        'current_date_from': filters['date_from'],
        'current_date_to': filters['date_to'],
        'current_mine': filters['mine'],
        'current_search': filters['search'],
    }
    
    return render(request, 'management/story/story_list.html', context)

# ============================================
# VACANCY VIEWS (Function-based)
# ============================================



@login_required
def vacancy_list(request):
    """List all vacancies with filters"""
    queryset = Vacancy.objects.select_related('author').order_by('-created_at')
    
    # Get filter parameters
    filters = {
        'status': request.GET.get('status', ''),
        'author': request.GET.get('author', ''),
        'job_type': request.GET.get('job_type', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
        'mine': request.GET.get('mine', ''),
        'search': request.GET.get('search', ''),
        'active': request.GET.get('active', ''),
        'featured': request.GET.get('featured', ''),
    }
    
    # Apply filters
    if filters['status'] == 'active':
        queryset = queryset.filter(is_active=True)
    elif filters['status'] == 'inactive':
        queryset = queryset.filter(is_active=False)
    
    if filters['active'] == 'true':
        queryset = queryset.filter(is_active=True)
    
    if filters['featured'] == 'true':
        queryset = queryset.filter(is_featured=True)
    
    if filters['author']:
        queryset = queryset.filter(author__username__icontains=filters['author'])
    
    if filters['job_type']:
        queryset = queryset.filter(job_type=filters['job_type'])
    
    # Search in title and organization
    if filters['search']:
        queryset = queryset.filter(
            Q(title__icontains=filters['search']) |
            Q(organization__icontains=filters['search']) |
            Q(location__icontains=filters['search'])
        )
    
    # Date range filters
    if filters['date_from']:
        try:
            date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=date_from)
        except (ValueError, TypeError):
            pass
    
    if filters['date_to']:
        try:
            date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=date_to)
        except (ValueError, TypeError):
            pass
    
    # My vacancies filter
    if filters['mine'] == 'true':
        queryset = queryset.filter(author=request.user)
    
    # Pagination
    per_page = request.GET.get('per_page', 20)
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 50, 100]:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20
    
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get counts
    total_count = Vacancy.objects.count()
    active_count = Vacancy.objects.filter(is_active=True).count()
    inactive_count = Vacancy.objects.filter(is_active=False).count()
    
    # Get unique job types for filter
    job_types = Vacancy.JOB_TYPES
    
    context = {
        'page_obj': page_obj,
        'vacancies': page_obj.object_list,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'job_types': job_types,
        'current_filters': filters,
        'current_per_page': per_page,
        'active_filter_count': sum(1 for v in filters.values() if v),
    }
    
    return render(request, 'management/vacancy/vacancy_list.html', context)




@login_required
@require_POST
def vacancy_toggle_active(request, pk):
    """Toggle vacancy active status"""
    try:
        vacancy = get_object_or_404(Vacancy, id=pk)
        
        # Check if user is author OR has 'Publisher' in roles
        is_author = vacancy.author == request.user
        is_publisher = hasattr(request.user, 'roles') and 'Publisher' in request.user.roles
        
        if not (is_author or is_publisher):
            return JsonResponse({
                'icon': 'error',
                'title': 'Permission Denied',
                'message': 'You do not have permission to modify this vacancy'
            }, status=403)
        
        vacancy.is_active = not vacancy.is_active
        vacancy.save()
        
        return JsonResponse({
            'icon': 'success',
            'title': 'Success!',
            'message': f'Vacancy marked as {"active" if vacancy.is_active else "inactive"}',
            'is_active': vacancy.is_active
        })
        
    except Vacancy.DoesNotExist:
        return JsonResponse({
            'icon': 'error',
            'title': 'Error',
            'message': 'Vacancy not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'icon': 'error',
            'title': 'Server Error',
            'message': 'An error occurred. Please try again.'
        }, status=500)


@login_required
@require_POST
def vacancy_toggle_featured(request, pk):
    """Toggle vacancy featured status"""
    try:
        vacancy = get_object_or_404(Vacancy, id=pk)
        
        # Check if user is author OR has 'Publisher' in roles
        is_author = vacancy.author == request.user
        is_publisher = hasattr(request.user, 'roles') and 'Publisher' in request.user.roles
        
        if not (is_author or is_publisher):
            return JsonResponse({
                'icon': 'error',
                'title': 'Permission Denied',
                'message': 'You do not have permission to modify this vacancy'
            }, status=403)
        
        vacancy.is_featured = not vacancy.is_featured
        vacancy.save()
        
        return JsonResponse({
            'icon': 'success',
            'title': 'Success!',
            'message': f'Vacancy {"featured" if vacancy.is_featured else "unfeatured"} successfully',
            'is_featured': vacancy.is_featured
        })
        
    except Vacancy.DoesNotExist:
        return JsonResponse({
            'icon': 'error',
            'title': 'Error',
            'message': 'Vacancy not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'icon': 'error',
            'title': 'Server Error',
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def vacancy_delete(request, pk):
    """Delete a vacancy"""
    try:
        vacancy = get_object_or_404(Vacancy, id=pk)
        
        # Check if user is author OR has 'Publisher' in roles
        is_author = vacancy.author == request.user
        is_publisher = hasattr(request.user, 'roles') and 'Publisher' in request.user.roles
        
        if not (is_author or is_publisher):
            return JsonResponse({
                'icon': 'error',
                'title': 'Permission Denied',
                'message': 'You do not have permission to delete this vacancy'
            }, status=403)
        
        # Delete attachments
        for attachment in vacancy.attachments:
            if attachment.file:
                attachment.file.delete()
            attachment.delete()
        
        vacancy.delete()
        
        # Get updated counts
        total_count = Vacancy.objects.count()
        active_count = Vacancy.objects.filter(is_active=True).count()
        inactive_count = Vacancy.objects.filter(is_active=False).count()
        featured_count = Vacancy.objects.filter(is_featured=True).count()
        
        return JsonResponse({
            'icon': 'success',
            'title': 'Success!',
            'message': 'Vacancy deleted successfully',
            'new_counts': {
                'total': total_count,
                'active': active_count,
                'inactive': inactive_count,
                'featured': featured_count,
            }
        })
        
    except Vacancy.DoesNotExist:
        return JsonResponse({
            'icon': 'error',
            'title': 'Error',
            'message': 'Vacancy not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'icon': 'error',
            'title': 'Server Error',
            'message': 'An error occurred. Please try again.'
        }, status=500)


@login_required
@require_POST
def attachment_delete(request, pk):
    """Delete a specific attachment"""
    try:
        attachment = get_object_or_404(GenericAttachment, id=pk)
        vacancy = attachment.content_object
        
        # Check permission: author or publisher
        is_author = vacancy.author == request.user
        is_publisher = hasattr(request.user, 'roles') and 'Publisher' in request.user.roles
        
        if not (is_author or is_publisher):
            return JsonResponse({
                'icon': 'error',
                'title': 'Permission Denied',
                'message': 'You do not have permission to delete this attachment'
            }, status=403)
        
        # Delete file and database record
        if attachment.file:
            attachment.file.delete()
        attachment.delete()
        
        return JsonResponse({
            'icon': 'success',
            'title': 'Success!',
            'message': 'Attachment deleted successfully'
        })
        
    except GenericAttachment.DoesNotExist:
        return JsonResponse({
            'icon': 'error',
            'title': 'Error',
            'message': 'Attachment not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'icon': 'error',
            'title': 'Server Error',
            'message': 'An error occurred. Please try again.'
        }, status=500)


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
@require_POST
def notice_delete(request, pk):
    """Delete a notice"""
    try:
        notice = get_object_or_404(Notice, id=pk)
        
        # Check if user is author OR has 'Publisher' in roles
        is_author = notice.author == request.user
        is_publisher = hasattr(request.user, 'roles') and 'Publisher' in request.user.roles
        
        if not (is_author or is_publisher):
            return JsonResponse({
                'icon': 'error',
                'title': 'Permission Denied',
                'message': 'You do not have permission to delete this notice'
            }, status=403)
        
        # Delete attachments
        for attachment in notice.attachments:
            if attachment.file:
                attachment.file.delete()
            attachment.delete()
        
        notice.delete()
        
        # Get updated counts
        total_count = Notice.objects.count()
        active_count = Notice.objects.filter(is_active=True).count()
        inactive_count = Notice.objects.filter(is_active=False).count()
        important_count = Notice.objects.filter(is_important=True).count()
        
        return JsonResponse({
            'icon': 'success',
            'title': 'Success!',
            'message': 'Notice deleted successfully',
            'new_counts': {
                'total': total_count,
                'active': active_count,
                'inactive': inactive_count,
                'important': important_count,
            }
        })
        
    except Notice.DoesNotExist:
        return JsonResponse({
            'icon': 'error',
            'title': 'Error',
            'message': 'Notice not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'icon': 'error',
            'title': 'Server Error',
            'message': 'An error occurred. Please try again.'
        }, status=500)



@login_required
def notice_list(request):
    """List all notices with filters"""
    queryset = Notice.objects.select_related('author').order_by('-publish_date', '-created_at')
    
    # Get filter parameters
    filters = {
        'category': request.GET.get('category', ''),
        'organization': request.GET.get('organization', ''),
        'status': request.GET.get('status', ''),
        'important': request.GET.get('important', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
        'mine': request.GET.get('mine', ''),
        'search': request.GET.get('search', ''),
    }
    
    # Apply filters
    if filters['category']:
        queryset = queryset.filter(category=filters['category'])
    
    if filters['organization']:
        queryset = queryset.filter(organization__icontains=filters['organization'])
    
    if filters['status'] == 'active':
        queryset = queryset.filter(is_active=True)
    elif filters['status'] == 'inactive':
        queryset = queryset.filter(is_active=False)
    elif filters['status'] == 'expired':
        queryset = [n for n in queryset if n.is_expired()]
        # Note: This is inefficient for large datasets. Consider adding a method to filter in DB.
    
    if filters['important'] == 'true':
        queryset = queryset.filter(is_important=True)
    
    # Search in headline and overview
    if filters['search']:
        queryset = queryset.filter(
            Q(headline__icontains=filters['search']) |
            Q(overview__icontains=filters['search']) |
            Q(organization__icontains=filters['search'])
        )
    
    # Date range filters
    if filters['date_from']:
        try:
            date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d').date()
            queryset = queryset.filter(publish_date__gte=date_from)
        except (ValueError, TypeError):
            pass
    
    if filters['date_to']:
        try:
            date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d').date()
            queryset = queryset.filter(publish_date__lte=date_to)
        except (ValueError, TypeError):
            pass
    
    # My notices filter
    if filters['mine'] == 'true':
        queryset = queryset.filter(author=request.user)
    
    # Pagination
    per_page = request.GET.get('per_page', 20)
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 50, 100]:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20
    
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get counts
    total_count = Notice.objects.count()
    active_count = Notice.objects.filter(is_active=True).count()
    inactive_count = Notice.objects.filter(is_active=False).count()
    important_count = Notice.objects.filter(is_important=True).count()
    
    context = {
        'page_obj': page_obj,
        'notices': page_obj.object_list,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'important_count': important_count,
        'categories': Notice.CATEGORIES,
        'current_filters': filters,
        'current_per_page': per_page,
        'active_filter_count': sum(1 for v in filters.values() if v),
    }
    
    return render(request, 'management/notice/notice_list.html', context)

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
                    return redirect('vacancy_page', pk=object_id)
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
        return redirect('vacancy_page', pk=obj.pk)
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