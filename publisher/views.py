from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib import messages
import threading
import json

from datetime import datetime

from .models import Story, Vacancy, Notice, Category
from .forms import StoryForm, VacancyForm, NoticeForm
from accounts.models import Subscriber, SiteInfo, TeamMember

from django.shortcuts import render, redirect
from django.http import FileResponse
from django.conf import settings
import os




# ==================== HTML PAGE VIEWS ====================


def team_member_page(request, pk):
    team_member = TeamMember.objects.get(id=pk)
    context = {
        'team_member': team_member,
    }
    return render(request, 'publisher/team_member_page.html', context)


def story_page(request, pk):
    """Render individual story page"""
    story = get_object_or_404(Story, id=pk)
    related_stories = Story.objects.filter(category=story.category)[:6]
    context = {
        'story': story, 
        'related_stories': related_stories,
    }
    return render(request, 'publisher/story_page.html', context)



def about_page(request):
    site_info = SiteInfo.objects.all().first()
    context = {
        'site_info': site_info,
    }
    
    return render(request, 'about.html', context)


def team_page(request):
    team_members = TeamMember.objects.filter(is_active=True).select_related('user').order_by('display_order', 'user__first_name')

    context = {
        'team_members': team_members,
    }
    return render(request, 'publisher/team_page.html', context)



def contact_page(request):
    """Render contact page with site information"""
    site_info = SiteInfo.objects.all().first()
    context = {
        'site_info': site_info,
    }
    return render(request, 'publisher/contact_page.html', context)



def vacancies_page(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'publisher/vacancies_page.html', context)


def stories_page(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'publisher/stories_page.html', context)


def notices_page(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'publisher/notices_page.html', context)


def home(request):
    featured_stories = Story.objects.all().order_by('-created_at')[:3]
    featured_vacancies = Vacancy.objects.all().order_by('-created_at')[:3]
    featured_notices = Notice.objects.all().order_by('-created_at')[:3]
    
    stories_published = Story.objects.filter(status="Published").count()
    jobs_listed = Vacancy.objects.filter(is_active=True).count()
    NGOs_engaged = "🔏"
    subscribers = Subscriber.objects.filter(is_active=True).count()
    context = {
        'featured_stories': featured_stories,
        'featured_vacancies': featured_vacancies,
        'featured_notices': featured_notices,

        'stories_published': stories_published,
        'jobs_listed': jobs_listed,
        'NGOs_engaged': NGOs_engaged,
        'subscribers': subscribers,
    }
    return render(request, 'home.html', context)




def privacy_terms_page(request):
    """Privacy & Terms download page"""
    context = {
        'current_date': datetime.now(),
    }
    return render(request, 'publisher/privacy_terms.html', context)

def download_privacy_terms(request):
    """Download the PDF file"""
    file_path = os.path.join(settings.STATIC_ROOT, 'documents', 'privacy_terms.pdf')
    
    # If using STATICFILES_DIRS instead of STATIC_ROOT
    if not os.path.exists(file_path):
        file_path = os.path.join(settings.BASE_DIR, 'static', 'documents', 'privacy_terms.pdf')
    
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Type'] = 'application/pdf'
        response['Content-Disposition'] = 'attachment; filename="NGO_News_Digest_Privacy_Terms.pdf"'
        return response
    else:
        # Fallback: redirect to a placeholder or show error
        return redirect('privacy_terms_page')

# ==================== EMAIL UTILITIES ====================

class EmailThread(threading.Thread):
    """Background thread for sending emails"""
    def __init__(self, subject, plain_message, html_message, recipient_list):
        super().__init__(daemon=True)
        self.subject = subject
        self.plain_message = plain_message
        self.html_message = html_message
        self.recipient_list = recipient_list

    def run(self):
        """Send emails in background thread"""
        for recipient in self.recipient_list:
            try:
                email = EmailMultiAlternatives(
                    subject=self.subject,
                    body=self.plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient],
                )
                if self.html_message:
                    email.attach_alternative(self.html_message, "text/html")
                email.send()
            except Exception as e:
                print(f"Failed to send email to {recipient}: {e}")


def send_email_in_background(subject, plain_message, html_message, recipient_list):
    """Start email sending in background thread"""
    if recipient_list:
        EmailThread(subject, plain_message, html_message, recipient_list).start()


# ==================== BLOG POST VIEWS ====================

def stories(request):
    """API endpoint for paginated stories"""
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 6))
    sort_by = request.GET.get('sort_by', 'created_at')
    sort_order = request.GET.get('sort_order', 'asc')
    
    stories_qs = Story.objects.all()
    
    # Apply sorting
    if sort_order.lower() == 'desc':
        sort_by = f'-{sort_by}'
    stories_qs = stories_qs.order_by(sort_by)
    
    # Pagination
    total_stories = stories_qs.count()
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_stories = stories_qs[start_index:end_index]
    
    stories_list = [
        {
            'id': story.id,
            'headline': story.headline,
            'snippet': story.snippet,
            'content': story.content,
            'author': f"{story.author.first_name} {story.author.last_name}",
            # For blank fields, check if they exist AND have content
            'author_twitter': story.author.team_profile.twitter_url if hasattr(story.author, 'team_profile') and story.author.team_profile.twitter_url else '',
            'author_linkedin': story.author.team_profile.linkedin_url if hasattr(story.author, 'team_profile') and story.author.team_profile.linkedin_url else '',
            'date_and_time': str(story.created_at)[:10],
            'image_url': story.get_thumbnail_url(),
            'category': story.category.name,
        }
        for story in paginated_stories
    ]
    
    return JsonResponse({"stories": stories_list})


def get_latest_stories(request):
    """API endpoint for latest published stories"""
    latest_stories = Story.objects.filter(status="PUBLISHED").order_by('-created_at')[:6]
    
    latest_stories_list = [
        {
            'id': story.id,
            'title': story.title,
            'snippet': strip_tags(f"{story.content[:200]}..."),
            'content': story.content,
            'author': f"{story.author.first_name} {story.author.last_name}",
            'date_and_time': str(story.created_at)[:10],
            'image_url': story.get_thumbnail_url(),
        }
        for story in latest_stories
    ]
    
    return JsonResponse({"stories": latest_stories_list})


def get_top_stories(request):
    """API endpoint for top stories"""
    top_stories = Story.objects.filter(status="PUBLISHED")[:6]
    
    top_stories_list = [
        {
            'id': story.id,
            'title': story.title,
            'snippet': strip_tags(f"{story.content[:200]}..."),
            'content': story.content,
            'author': f"{story.author.first_name} {story.author.last_name}",
            'date_and_time': str(story.created_at)[:10],
            'image_url': story.get_thumbnail_url(),
        }
        for story in top_stories
    ]
    
    return JsonResponse({"stories": top_stories_list})


def get_editors_pick_stories(request):
    """API endpoint for editors pick stories"""
    editors_pick_stories = Story.objects.filter(status="PUBLISHED")[:6]
    
    editors_pick_stories_list = [
        {
            'id': story.id,
            'title': story.title,
            'snippet': strip_tags(f"{story.content[:200]}..."),
            'content': story.content,
            'author': f"{story.author.first_name} {story.author.last_name}",
            'date_and_time': str(story.created_at)[:10],
            'image_url': story.get_thumbnail_url(),
        }
        for story in editors_pick_stories
    ]
    
    return JsonResponse({"stories": editors_pick_stories_list})


@login_required
def upload_blog_post(request):
    """Upload and publish blog post"""
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.status = 'PUBLISHED'
            post.published_at = timezone.now()
            post.save()
            
            # Notify subscribers
            notify_subscribers(post.id)
            
            return JsonResponse({
                'success': True,
                'message': 'Post uploaded and published successfully!',
                'post_id': post.id,
                'title': post.title,
                'status': post.status
            })
        
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })
    
    form = StoryForm()
    return render(request, 'blog/upload.html', {'form': form})


def notify_subscribers(post_id):
    """Notify subscribers about new post"""
    try:
        post = Story.objects.get(id=post_id)
        site_url = settings.SITE_URL or 'http://localhost:8000'
        
        # Get active verified subscribers
        subscribers = Subscriber.objects.filter(
            is_active=True, 
            is_verified=True
        ).values_list('email', flat=True)
        
        if not subscribers.exists():
            return
        
        # Create email content
        subject = f"📰 New Story: {post.title}"
        html_message = render_to_string('emails/new_story.html', {
            'post': post,
            'site_url': site_url,
        })
        
        plain_message = f"""
        📰 New Story: {post.title}
        
        {strip_tags(post.content)[:200]}...
        
        Read the full story: {site_url}/publisher/story/{post.id}/
        
        Best regards,
        NGO News Digest Team
        """
        
        # Send in background
        send_email_in_background(subject, plain_message, html_message, list(subscribers))
        
    except Story.DoesNotExist:
        print(f"Post {post_id} not found")
    except Exception as e:
        print(f"Error in notify_subscribers: {e}")


def success_page(request):
    """Show success page after post upload"""
    latest_post = None
    if request.user.is_authenticated:
        latest_post = Story.objects.filter(author=request.user).order_by('-created_at').first()
    
    return render(request, 'blog/success.html', {
        'latest_post': latest_post,
    })


# ==================== VACANCY VIEWS ====================

def vacancies(request):
    """API endpoint for paginated stories"""
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 6))
    sort_by = request.GET.get('sort_by', 'created_at')
    sort_order = request.GET.get('sort_order', 'asc')
    
    vacancies_qs = Vacancy.objects.all()
    
    # Apply sorting
    if sort_order.lower() == 'desc':
        sort_by = f'-{sort_by}'
    vacancies_qs = vacancies_qs.order_by(sort_by)
    
    # Pagination
    total_vacancies = vacancies_qs.count()
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_vacancies = vacancies_qs[start_index:end_index]
    
    vacancies_list = [
        {
            'id': vacancy.id,
            'title': vacancy.title,
            'organization': vacancy.organization,
            'description': vacancy.description,
            'location': vacancy.location,
            'job_type': vacancy.job_type,
            'application_deadline': vacancy.application_deadline,
            'expiration_date': vacancy.expiration_date,
            'created_at': vacancy.created_at,
            'organization': vacancy.organization,
        }
        for vacancy in paginated_vacancies
    ]
    
    return JsonResponse({"vacancies": vacancies_list})


def vacancy_page(request, pk):
    vacancy = Vacancy.objects.get(id=pk)
    
    # Extract key words from current title
    current_words = set(vacancy.title.lower().split())
    
    # Filter for vacancies with at least 2 matching words
    all_vacancies = Vacancy.objects.exclude(id=pk)
    similar_jobs = []
    
    for other_vacancy in all_vacancies:
        other_words = set(other_vacancy.title.lower().split())
        
        # Count common words
        common_words = current_words.intersection(other_words)
        
        # If they share at least 2 meaningful words (excluding short/common words)
        meaningful_words = {word for word in common_words if len(word) > 3}
        if len(meaningful_words) >= 2:
            similar_jobs.append(other_vacancy)
        
        # Limit results
        if len(similar_jobs) >= 3:
            break
    
    context = {
        'vacancy': vacancy,
        'similar_jobs': similar_jobs,
    }
    
    return render(request, 'publisher/vacancy_page.html', context)


def get_vacancies(request):
    """API for homepage vacancies"""
    # Featured vacancies
    featured = Vacancy.objects.filter(
        is_active=True,
        is_featured=True,
        application_deadline__gte=timezone.now().date()
    )[:4]
    
    # Recent vacancies
    recent = Vacancy.objects.filter(
        is_active=True,
        application_deadline__gte=timezone.now().date()
    ).order_by('-created_at')[:4]
    
    featured_list = [
        {
            'id': v.id,
            'title': v.title,
            'organization': v.organization,
            'location': v.location,
            'job_type': v.get_job_type_display(),
            'deadline': v.application_deadline.strftime('%b %d'),
            'days_left': v.days_remaining(),
        }
        for v in featured
    ]
    
    recent_list = [
        {
            'id': v.id,
            'title': v.title,
            'organization': v.organization,
            'location': v.location,
            'job_type': v.get_job_type_display(),
        }
        for v in recent
    ]
    
    return JsonResponse({
        'featured': featured_list,
        'recent': recent_list,
    })


@login_required
def upload_vacancy(request):
    """Upload new vacancy"""
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        if form.is_valid():
            vacancy = form.save()
            messages.success(request, 'Vacancy posted successfully!')
            return redirect('vacancy_detail', pk=vacancy.id)
    
    form = VacancyForm()
    return render(request, 'vacancies/upload.html', {'form': form})


@login_required
def ajax_upload_vacancy(request):
    """AJAX endpoint for vacancy upload"""
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        if form.is_valid():
            vacancy = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Vacancy posted successfully!',
                'id': vacancy.id,
                'title': vacancy.title,
                'url': f'/vacancies/{vacancy.id}/'
            })
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


# ==================== NOTICE VIEWS ====================

def notices(request):
    """API endpoint for paginated stories"""
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 6))
    sort_by = request.GET.get('sort_by', 'created_at')
    sort_order = request.GET.get('sort_order', 'asc')
    
    notices_qs = Notice.objects.all()
    
    # Apply sorting
    if sort_order.lower() == 'desc':
        sort_by = f'-{sort_by}'
    notices_qs = notices_qs.order_by(sort_by)
    
    # Pagination
    total_notices = notices_qs.count()
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_notices = notices_qs[start_index:end_index]
    
    notices_list = [
        {
            'id': notice.id,
            'headline': notice.headline,
            'overview': notice.overview,
            'description': notice.description,
            'organization': notice.organization,
            'category': notice.category,
            'publish_date': notice.publish_date,
            'expiration_date': notice.expiration_date,
        }
        for notice in paginated_notices
    ]
    
    return JsonResponse({"notices": notices_list})


def notice_page(request, pk):
    notice = Notice.objects.get(id=pk)
    related_notices = Notice.objects.filter(category=notice.category)[:6]
    context = {
        'notice': notice,
        'related_notices': related_notices,
    }
    
    return render(request, 'publisher/notice_page.html', context)


def get_notices(request):
    """API for homepage notices"""
    # Important notices
    important = Notice.objects.filter(
        is_active=True,
        is_important=True
    )[:4]
    
    # Recent notices
    recent = Notice.objects.filter(is_active=True).order_by('-created_at')[:4]
    
    important_list = [
        {
            'id': n.id,
            'title': n.title,
            'description': n.description[:100] + '...' if len(n.description) > 100 else n.description,
            'organization': n.organization,
            'category': n.get_category_display(),
            'has_file': bool(n.attachment),
        }
        for n in important
    ]
    
    recent_list = [
        {
            'id': n.id,
            'title': n.title,
            'description': n.description[:80] + '...' if len(n.description) > 80 else n.description,
            'organization': n.organization,
        }
        for n in recent
    ]
    
    return JsonResponse({
        'important': important_list,
        'recent': recent_list,
    })


@login_required
def upload_notice(request):
    """Upload new notice"""
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save()
            messages.success(request, 'Notice posted successfully!')
            return redirect('notice_detail', pk=notice.id)
    
    form = NoticeForm()
    return render(request, 'notices/upload.html', {'form': form})


@login_required
def ajax_upload_notice(request):
    """AJAX endpoint for notice upload"""
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Notice posted successfully!',
                'id': notice.id,
                'title': notice.title,
                'url': f'/notices/{notice.id}/'
            })
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


# ==================== SUBSCRIBER MANAGEMENT ====================

@login_required
def subscriber_list(request):
    """View all subscribers with pagination"""
    search_query = request.GET.get('q', '')
    
    subscribers = Subscriber.objects.all().order_by('-subscribed_at')
    
    if search_query:
        subscribers = subscribers.filter(
            Q(email__icontains=search_query) |
            Q(name__icontains=search_query)
        )
    
    paginator = Paginator(subscribers, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'subscriptions/subscriber_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_subscribers': subscribers.count(),
        'active_subscribers': Subscriber.objects.filter(is_active=True, is_verified=True).count(),
    })


def unsubscribe_link(request, email):
    """One-click unsubscribe link"""
    try:
        subscriber = Subscriber.objects.get(email=email)
        subscriber.is_active = False
        subscriber.save()
        
        return render(request, 'subscriptions/unsubscribe_success.html', {
            'email': email,
            'message': 'You have been unsubscribed successfully.'
        })
    except Subscriber.DoesNotExist:
        return render(request, 'subscriptions/unsubscribe_success.html', {
            'email': email,
            'message': 'Email not found in our subscription list.'
        })