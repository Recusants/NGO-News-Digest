# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from publisher.models import BlogPost, Category

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .forms import BlogPostForm
from publisher.models import BlogPost


from django.contrib.auth import authenticate, login as built_inn_login_function
from django.contrib.auth import logout as log_out

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from publisher.models import Vacancy, Notice
from .forms import VacancyForm, NoticeForm




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from accounts.models import Subscriber
from .forms import SubscriberForm

# ========== SUBSCRIBER VIEWS ==========


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import csv
from django.http import HttpResponse





from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.db.models import Q
from accounts.models import User, TeamMember, SiteInfo
from .forms import UserProfileForm, ChangePasswordForm, TeamMemberForm, SiteInfoForm

# ========== USER PROFILE VIEWS ==========

@login_required
def profile_view(request):
    """View and edit user profile"""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user, request=request)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user, request=request)
    
    # Get password change form
    password_form = ChangePasswordForm(user=user)
    
    context = {
        'title': 'My Profile',
        'form': form,
        'password_form': password_form,
        'user': user,
    }
    return render(request, 'management/profile.html', context)

@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            request.user.set_password(new_password)
            request.user.save()
            
            # Keep user logged in after password change
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
        else:
            # If password change fails, show profile page with errors
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'management/profile.html', {
                'title': 'My Profile',
                'form': UserProfileForm(instance=request.user, request=request),
                'password_form': form,
                'user': request.user,
            })
    
    return redirect('profile')

# ========== TEAM MEMBER VIEWS ==========

@login_required
def team_member_list(request):
    """List all team members"""
    team_members = TeamMember.objects.all().order_by('display_order', 'user__first_name')
    
    context = {
        'team_members': team_members,
        'title': 'Team Members',
        'total_count': team_members.count(),
        'active_count': team_members.filter(is_active=True).count(),
    }
    return render(request, 'management/team_member_list.html', context)

@login_required
def team_member_create(request):
    """Create new team member"""
    if request.method == 'POST':
        form = TeamMemberForm(request.POST)
        if form.is_valid():
            team_member = form.save()
            messages.success(request, f'Team member "{team_member.user.get_full_name()}" created successfully!')
            return redirect('team_member_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeamMemberForm()
    
    context = {
        'form': form,
        'title': 'Add Team Member',
    }
    return render(request, 'management/team_member_form.html', context)

@login_required
def team_member_edit(request, pk):
    """Edit team member"""
    team_member = get_object_or_404(TeamMember, pk=pk)
    
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, instance=team_member)
        if form.is_valid():
            team_member = form.save()
            messages.success(request, f'Team member "{team_member.user.get_full_name()}" updated successfully!')
            return redirect('team_member_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeamMemberForm(instance=team_member)
    
    context = {
        'form': form,
        'title': 'Edit Team Member',
        'team_member': team_member,
    }
    return render(request, 'management/team_member_form.html', context)

@login_required
def team_member_delete(request, pk):
    """Delete team member"""
    if request.method == 'POST':
        team_member = get_object_or_404(TeamMember, pk=pk)
        name = team_member.user.get_full_name()
        team_member.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f'Team member "{name}" deleted successfully!'
            })
        
        messages.success(request, f'Team member "{name}" deleted successfully!')
        return redirect('team_member_list')
    
    return redirect('team_member_list')

@login_required
def team_member_toggle_active(request, pk):
    """Toggle team member active status"""
    if request.method == 'POST':
        team_member = get_object_or_404(TeamMember, pk=pk)
        team_member.is_active = not team_member.is_active
        team_member.save()
        
        status = 'activated' if team_member.is_active else 'deactivated'
        message = f'Team member "{team_member.user.get_full_name()}" {status} successfully!'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': message,
                'is_active': team_member.is_active
            })
        
        messages.success(request, message)
        return redirect('team_member_list')
    
    return redirect('team_member_list')

# ========== SITE SETTINGS VIEWS ==========

@login_required
def site_settings(request):
    """Edit site settings"""
    site_info, created = SiteInfo.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        form = SiteInfoForm(request.POST, instance=site_info)
        if form.is_valid():
            form.save()
            messages.success(request, 'Site settings updated successfully!')
            return redirect('site_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SiteInfoForm(instance=site_info)
    
    context = {
        'form': form,
        'title': 'Site Settings',
        'site_info': site_info,
        'last_updated': site_info.updated_at,
    }
    return render(request, 'management/site_settings.html', context)

@login_required
def export_subscribers_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Status', 'Verified', 'Subscribed At', 'Verified At'])
    
    subscribers = Subscriber.objects.all().order_by('-subscribed_at')
    for subscriber in subscribers:
        writer.writerow([
            subscriber.name,
            subscriber.email,
            'Active' if subscriber.is_active else 'Inactive',
            'Yes' if subscriber.is_verified else 'No',
            subscriber.subscribed_at.strftime('%Y-%m-%d %H:%M'),
            subscriber.verified_at.strftime('%Y-%m-%d %H:%M') if subscriber.verified_at else ''
        ])
    
    return response

@login_required
def subscriber_list(request):
    subscribers_list = Subscriber.objects.all().order_by('-subscribed_at')
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    verification_filter = request.GET.get('verification', 'all')
    
    if status_filter == 'active':
        subscribers_list = subscribers_list.filter(is_active=True)
    elif status_filter == 'inactive':
        subscribers_list = subscribers_list.filter(is_active=False)
    
    if verification_filter == 'verified':
        subscribers_list = subscribers_list.filter(is_verified=True)
    elif verification_filter == 'unverified':
        subscribers_list = subscribers_list.filter(is_verified=False)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(subscribers_list, 20)  # 20 items per page
    
    try:
        subscribers = paginator.page(page)
    except PageNotAnInteger:
        subscribers = paginator.page(1)
    except EmptyPage:
        subscribers = paginator.page(paginator.num_pages)
    
    total_count = Subscriber.objects.count()
    active_count = Subscriber.objects.filter(is_active=True).count()
    verified_count = Subscriber.objects.filter(is_verified=True).count()
    unverified_count = total_count - verified_count  # Calculate here
    
    context = {
        'subscribers': subscribers,
        'title': 'Subscribers',
        'total_count': total_count,
        'active_count': active_count,
        'verified_count': verified_count,
        'unverified_count': unverified_count,  # Add this
        'current_filters': {
            'status': status_filter,
            'verification': verification_filter
        }
    }
    return render(request, 'management/subscriber_list.html', context)

@login_required
def subscriber_delete(request, pk):
    if request.method == 'POST':
        subscriber = get_object_or_404(Subscriber, pk=pk)
        email = subscriber.email
        subscriber.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f'Subscriber "{email}" deleted successfully!'
            })
        
        messages.success(request, f'Subscriber "{email}" deleted successfully!')
        return redirect('subscriber_list')
    
    return redirect('subscriber_list')

@login_required
def subscriber_toggle_active(request, pk):
    if request.method == 'POST':
        subscriber = get_object_or_404(Subscriber, pk=pk)
        subscriber.is_active = not subscriber.is_active
        subscriber.save()
        
        status = 'activated' if subscriber.is_active else 'deactivated'
        message = f'Subscriber "{subscriber.email}" {status} successfully!'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': message,
                'is_active': subscriber.is_active
            })
        
        messages.success(request, message)
        return redirect('subscriber_list')
    
    return redirect('subscriber_list')

@login_required
def subscriber_verify(request, pk):
    if request.method == 'POST':
        subscriber = get_object_or_404(Subscriber, pk=pk)
        if not subscriber.is_verified:
            subscriber.is_verified = True
            subscriber.verified_at = timezone.now()
            subscriber.save()
            
            message = f'Subscriber "{subscriber.email}" marked as verified!'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': message,
                    'is_verified': subscriber.is_verified
                })
            
            messages.success(request, message)
        return redirect('subscriber_list')
    
    return redirect('subscriber_list')

@login_required
def subscriber_unsubscribe(request, pk):
    if request.method == 'POST':
        subscriber = get_object_or_404(Subscriber, pk=pk)
        if subscriber.is_active:
            subscriber.is_active = False
            subscriber.save()
            
            message = f'Subscriber "{subscriber.email}" has been unsubscribed!'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': message,
                    'is_active': subscriber.is_active
                })
            
            messages.success(request, message)
        return redirect('subscriber_list')
    
    return redirect('subscriber_list')

@login_required
def bulk_delete_subscribers(request):
    if request.method == 'POST':
        subscriber_ids = request.POST.getlist('subscriber_ids[]')
        
        if not subscriber_ids:
            messages.error(request, 'No subscribers selected for deletion.')
            return redirect('subscriber_list')
        
        deleted_count = 0
        for pk in subscriber_ids:
            try:
                subscriber = Subscriber.objects.get(pk=pk)
                subscriber.delete()
                deleted_count += 1
            except Subscriber.DoesNotExist:
                continue
        
        messages.success(request, f'{deleted_count} subscriber(s) deleted successfully!')
        return redirect('subscriber_list')
    
    return redirect('subscriber_list')







# ========== VACANCY VIEWS ==========

@login_required
def vacancy_list(request):
    vacancies = Vacancy.objects.all().order_by('-created_at')
    return render(request, 'management/vacancy_list.html', {
        'vacancies': vacancies,
        'title': 'Vacancies'
    })

@login_required
def vacancy_create(request):
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        if form.is_valid():
            vacancy = form.save()
            messages.success(request, f'Vacancy "{vacancy.title}" created successfully!')
            return redirect('vacancy_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VacancyForm()
    
    return render(request, 'management/vacancy_form.html', {
        'form': form,
        'title': 'Create Vacancy'
    })

@login_required
def vacancy_edit(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    
    if request.method == 'POST':
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            vacancy = form.save()
            messages.success(request, f'Vacancy "{vacancy.title}" updated successfully!')
            return redirect('vacancy_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VacancyForm(instance=vacancy)
    
    return render(request, 'management/vacancy_form.html', {
        'form': form,
        'title': 'Edit Vacancy',
        'vacancy': vacancy
    })

@login_required
def vacancy_delete(request, pk):
    if request.method == 'POST':
        vacancy = get_object_or_404(Vacancy, pk=pk)
        title = vacancy.title
        vacancy.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f'Vacancy "{title}" deleted successfully!'
            })
        
        messages.success(request, f'Vacancy "{title}" deleted successfully!')
        return redirect('vacancy_list')
    
    return redirect('vacancy_list')

@login_required
def vacancy_toggle_active(request, pk):
    if request.method == 'POST':
        vacancy = get_object_or_404(Vacancy, pk=pk)
        vacancy.is_active = not vacancy.is_active
        vacancy.save()
        
        status = 'activated' if vacancy.is_active else 'deactivated'
        message = f'Vacancy "{vacancy.title}" {status} successfully!'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': message,
                'is_active': vacancy.is_active
            })
        
        messages.success(request, message)
        return redirect('vacancy_list')
    
    return redirect('vacancy_list')

# ========== NOTICE VIEWS ==========

@login_required
def notice_list(request):
    notices = Notice.objects.all().order_by('-created_at')
    return render(request, 'management/notice_list.html', {
        'notices': notices,
        'title': 'Notices'
    })

@login_required
def notice_create(request):
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save()
            messages.success(request, f'Notice "{notice.title}" created successfully!')
            return redirect('notice_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = NoticeForm()
    
    return render(request, 'management/notice_form.html', {
        'form': form,
        'title': 'Create Notice'
    })

@login_required
def notice_edit(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES, instance=notice)
        if form.is_valid():
            notice = form.save()
            messages.success(request, f'Notice "{notice.title}" updated successfully!')
            return redirect('notice_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = NoticeForm(instance=notice)
    
    return render(request, 'management/notice_form.html', {
        'form': form,
        'title': 'Edit Notice',
        'notice': notice
    })

@login_required
def notice_delete(request, pk):
    if request.method == 'POST':
        notice = get_object_or_404(Notice, pk=pk)
        title = notice.title
        
        # Delete attached file if exists
        if notice.attachment:
            notice.attachment.delete(save=False)
        
        notice.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f'Notice "{title}" deleted successfully!'
            })
        
        messages.success(request, f'Notice "{title}" deleted successfully!')
        return redirect('notice_list')
    
    return redirect('notice_list')

@login_required
def notice_toggle_active(request, pk):
    if request.method == 'POST':
        notice = get_object_or_404(Notice, pk=pk)
        notice.is_active = not notice.is_active
        notice.save()
        
        status = 'activated' if notice.is_active else 'deactivated'
        message = f'Notice "{notice.title}" {status} successfully!'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': message,
                'is_active': notice.is_active
            })
        
        messages.success(request, message)
        return redirect('notice_list')
    
    return redirect('notice_list')



def login_page(request):
    return render(request, 'management/login_page.html')

@require_POST
@csrf_exempt
def login(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Please enter both username and password'
            })
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'message': f'Welcome back, {user.username}!'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'This account is inactive'
                })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username or password'
            })
    
    # Regular POST request (fallback)
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()
    
    if not username or not password:
        messages.error(request, 'Please enter both username and password')
        return redirect('login_page')
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            return redirect("management")
        else:
            messages.error(request, 'This account is inactive')
            return redirect('login_page')
    else:
        messages.error(request, 'Invalid username or password')
        return redirect('login_page')

@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('login_page')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'management/password_reset_form.html'
    email_template_name = 'management/password_reset_email.html'
    subject_template_name = 'management/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        users = form.get_users(email)
        
        if users:
            return super().form_valid(form)
        else:
            messages.error(self.request, 'No user found with that email address.')
            return self.form_invalid(form)

# AJAX password reset endpoint
@require_POST
@csrf_exempt
def ajax_send_reset_email(request):
    email = request.POST.get('email', '').strip()
    
    if not email:
        return JsonResponse({
            'status': 'error',
            'message': 'Please enter your email address'
        })
    
    # Check if user exists with this email
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'No user found with that email address'
        })
    
    # Generate reset token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build reset URL
    reset_url = request.build_absolute_uri(
        reverse_lazy('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    )
    
    # Send email
    subject = 'Password Reset Request'
    message = render_to_string('management/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
        'site_name': request.get_host(),
    })
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Password reset email sent successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to send email: {str(e)}'
        })




@login_required
def blog_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user

            if post.status == 'PUBLISHED':
                post.published_at = timezone.now()

            post.save()
            return redirect('story_page', post.id)
    else:
        form = BlogPostForm()

    return render(request, 'management/create_story_form.html', {
        'form': form,
        'title': 'Create Blog Post'
    })



@login_required
def blog_edit(request, pk):
    post = get_object_or_404(BlogPost, pk=pk, author=request.user)

    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)

            if post.status == 'PUBLISHED' and post.published_at is None:
                post.published_at = timezone.now()

            post.save()
            return redirect('story_page', post.id)
    else:
        form = BlogPostForm(instance=post)

    return render(request, 'management/create_story_form.html', {
        'form': form,
        'title': 'Edit Blog Post'
    })


@login_required
def management_story_list_page(request):
	return render(request, 'management/management_story_list_page.html')



@login_required
def management_stories(request):
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 6))
    category = request.GET.get('category', '')
    sort_by = request.GET.get('sort_by', 'created_at')
    sort_order = request.GET.get('sort_order', 'asc')
    

    # Start with all stories
    stories = BlogPost.objects.all()
    
    # Apply sorting
    if sort_order.lower() == 'desc':
        sort_by = f'-{sort_by}'

    stories = stories.order_by(sort_by)
    
    # Calculate pagination
    total_stories = stories.count()
    total_pages = (total_stories + page_size - 1) // page_size
    
    # Apply pagination
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_stories = stories[start_index:end_index]


    stories_list = [
        {
            'id': story.id,
            'id_sys': story.system_id,
            'title': story.title,
            'snippet': "Story snippet mist be here. Story snippet mist be custome and come here. Story and come here. Story snippet mist be custome and come here",
            'content': story.content,
            'author': f"{story.author.first_name} {story.author.last_name}",
            'author_twitter': f"{story.author.twitter}",
            'author_facebook': f"{story.author.facebook}",
            'date_and_time': str(story.created_at)[:10],
            'image_url': story.get_thumbnail_url(),
            'category': story.category.name if story.category else "",
            'status': story.status,
        }
        for story in paginated_stories
    ]
    
    return JsonResponse({
        "stories": stories_list,
    })



@login_required
def management_page(request):
	total_stories = 100
	new_stories = 100
	stories_published = 100
	publishing_rate = 100
	pending = 100
	subscribers = 100
	new_subscribers = 100
	context = {
		'total_stories': total_stories,
		'new_stories': new_stories,
		'stories_published': stories_published,
		'publishing_rate': publishing_rate,
		'pending': pending,
		'subscribers': subscribers,
		'new_subscribers': new_subscribers,
	}
	return render(request, 'management/management_page.html', context)




