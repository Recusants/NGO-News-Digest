from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import BlogPost, Vacancy, Notice
from .forms import BlogPostForm, VacancyForm, NoticeForm
import json
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string
import threading
from django.utils import timezone
from datetime import timedelta

from accounts.models import Subscriber

from django.contrib import messages




# Email sending in background thread
class EmailThread(threading.Thread):
    def __init__(self, subject, plain_message, html_message, recipient_list):
        self.subject = subject
        self.plain_message = plain_message
        self.html_message = html_message
        self.recipient_list = recipient_list
        threading.Thread.__init__(self)
        self.daemon = True  # Make thread daemon so it doesn't block exit

    def run(self):
        try:
            # Send to each recipient individually to avoid issues
            for recipient in self.recipient_list:
                try:
                    email = EmailMultiAlternatives(
                        subject=self.subject,
                        body=self.plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[recipient],  # Send to individual recipient
                    )
                    if self.html_message:
                        email.attach_alternative(self.html_message, "text/html")
                    email.send()
                    print(f"✓ Email sent to: {recipient}")
                except Exception as e:
                    print(f"✗ Failed to send to {recipient}: {e}")
        except Exception as e:
            print(f"✗ Thread error: {e}")


def send_email_in_background(subject, plain_message, html_message, recipient_list):
    """Send email in background thread"""
    if recipient_list:  # Only start if there are recipients
        EmailThread(subject, plain_message, html_message, recipient_list).start()


def home(request):

    print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
    print(settings.DEBUG)
    return render(request, 'home.html')


def story(request, pk):
    story = BlogPost.objects.get(id=pk)
    related_stories = BlogPost.objects.filter(status='PUBLISHED').exclude(id=pk)[:3]
    context = {
        'story': story,
        'related_stories': related_stories,
    }
    return render(request, 'content/story.html', context)



def stories(request):
    latest_stories = BlogPost.objects.filter(status="PUBLISHED").order_by('-created_at')[:50]

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
    
    return JsonResponse({
        "stories": latest_stories_list,
    })


def get_latest_stories(request):
    latest_stories = BlogPost.objects.filter(status="PUBLISHED").order_by('-created_at')[:6]

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
    
    return JsonResponse({
        "stories": latest_stories_list,
    })


def get_top_stories(request):
    top_stories = BlogPost.objects.filter(status="PUBLISHED")[:6]

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
    
    return JsonResponse({
        "stories": top_stories_list,
    })


def get_editors_pick_stories(request):
    editors_pick_stories = BlogPost.objects.filter(status="PUBLISHED")[:6]

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
    
    return JsonResponse({
        "stories": editors_pick_stories_list,
    })


@login_required
def upload_blog_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            
            print(f"📝 Form data received:")
            print(f"  Title: {post.title}")
            print(f"  Status from form: {post.status}")
            print(f"  Content length: {len(post.content or '')}")
            
            # Make sure status is PUBLISHED
            if post.status != 'PUBLISHED':
                print(f"⚠️ Status is '{post.status}', changing to 'PUBLISHED'")
                post.status = 'PUBLISHED'
            
            # Set published date
            post.published_at = timezone.now()
            
            post.save()
            
            print(f"✅ Blog post saved: {post.title} (ID: {post.id}, Status: {post.status})")
            print(f"✅ Published at: {post.published_at}")
            
            # Send to subscribers
            print("📧 Starting subscriber notification...")
            notify_subscribers(post.id)
            
            # Return JSON response for AJAX
            return JsonResponse({
                'success': True,
                'message': 'Post uploaded and published successfully!',
                'post_id': post.id,
                'title': post.title,
                'status': post.status
            })
        else:
            print(f"❌ Form errors: {form.errors}")
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    form = BlogPostForm()
    return render(request, 'blog/upload.html', {'form': form})


def notify_subscribers(post_id):
    """Notify subscribers about new post in background"""
    print(f"🚀 Starting notify_subscribers for post {post_id}")
    
    try:
        post = BlogPost.objects.get(id=post_id)
        site_url = settings.SITE_URL or 'http://localhost:8000'
        
        print(f"📰 Found post: {post.title}")
        
        # Get active verified subscribers
        subscribers = Subscriber.objects.filter(
            is_active=True, 
            is_verified=True
        ).values_list('email', flat=True)
        
        subscriber_count = subscribers.count()
        print(f"👥 Found {subscriber_count} active subscribers")
        
        if subscriber_count == 0:
            print("⚠️ No active subscribers to notify")
            return
        
        # Create email content
        subject = f"📰 New Story: {post.title}"
        
        # Generate HTML email
        html_message = render_to_string('emails/new_story.html', {
            'post': post,
            'site_url': site_url,
        })
        
        # Generate plain text version
        plain_message = f"""
        📰 New Story: {post.title}
        
        {strip_tags(post.content)[:200]}...
        
        Read the full story: {site_url}/publisher/story/{post.id}/
        
        Best regards,
        NGO News Digest Team
        
        You're receiving this email because you subscribed to NGO News Digest.
        Don't want to receive these emails anymore? {site_url}/subscriptions/unsubscribe/
        """
        
        # Convert to list
        subscriber_list = list(subscribers)
        
        # For testing: Send to first 2 subscribers immediately
        test_emails = subscriber_list[:2] if len(subscriber_list) > 2 else subscriber_list
        print(f"🧪 Sending test emails to: {test_emails}")
        
        # Send test emails immediately (not in background)
        for email in test_emails:
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                    html_message=html_message,
                )
                print(f"✅ Test email sent to: {email}")
            except Exception as e:
                print(f"❌ Failed to send test email to {email}: {e}")
        
        # Send remaining emails in background
        if len(subscriber_list) > 2:
            remaining_emails = subscriber_list[2:]
            print(f"🔄 Queuing {len(remaining_emails)} remaining emails for background sending")
            
            # Send in smaller batches
            batch_size = 10  # Smaller batch for testing
            for i in range(0, len(remaining_emails), batch_size):
                batch = remaining_emails[i:i + batch_size]
                print(f"📤 Starting background thread for batch {i//batch_size + 1} ({len(batch)} emails)")
                send_email_in_background(subject, plain_message, html_message, batch)
        
        print(f"🎉 Notification process completed for post {post_id}")
        
    except BlogPost.DoesNotExist:
        print(f"❌ Post {post_id} not found")
    except Exception as e:
        print(f"💥 Error in notify_subscribers: {str(e)}")
        import traceback
        traceback.print_exc()


def success_view(request):
    return render(request, 'blog/success.html')


# Subscriber management views
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
    
    paginator = Paginator(subscribers, 50)  # Show 50 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'subscriptions/subscriber_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_subscribers': subscribers.count(),
        'active_subscribers': Subscriber.objects.filter(is_active=True, is_verified=True).count(),
    })


@login_required
def export_subscribers(request):
    """Export subscribers to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Email', 'Name', 'Verified', 'Active', 'Subscribed Date', 'Verified Date'])
    
    subscribers = Subscriber.objects.filter(is_active=True, is_verified=True)
    for subscriber in subscribers:
        writer.writerow([
            subscriber.email,
            subscriber.name,
            'Yes' if subscriber.is_verified else 'No',
            'Yes' if subscriber.is_active else 'No',
            subscriber.subscribed_at.strftime('%Y-%m-%d') if subscriber.subscribed_at else '',
            subscriber.verified_at.strftime('%Y-%m-%d') if subscriber.verified_at else '',
        ])
    
    return response


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


# Add a direct email test function
def test_email_direct(request):
    """Direct email test function"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            return JsonResponse({'success': False, 'error': 'Email required'})
        
        try:
            subject = "📧 Test Email from NGO News"
            message = "This is a test email to check if email sending is working."
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            return JsonResponse({'success': True, 'message': f'Test email sent to {email}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'blog/test_email.html')


def success_page(request):
    """Show success page after post upload"""
    # Get the latest post by the current user if available
    latest_post = None
    if request.user.is_authenticated:
        latest_post = BlogPost.objects.filter(author=request.user).order_by('-created_at').first()
    
    return render(request, 'blog/success.html', {
        'latest_post': latest_post,
    })






# ==================== VACANCIES ====================

def vacancy_list(request):
    """Simple vacancy list"""
    search = request.GET.get('search', '')
    job_type = request.GET.get('type', '')
    
    vacancies = Vacancy.objects.filter(is_active=True)
    
    if search:
        vacancies = vacancies.filter(
            Q(title__icontains=search) |
            Q(organization__icontains=search) |
            Q(location__icontains=search)
        )
    
    if job_type:
        vacancies = vacancies.filter(job_type=job_type)
    
    return render(request, 'vacancies/list.html', {
        'vacancies': vacancies,
        'search': search,
        'job_type': job_type,
        'job_types': Vacancy.JOB_TYPES,
    })


def vacancy_detail(request, pk):
    """Vacancy detail view - Show even if not active"""
    try:
        # First try to get the vacancy (including inactive ones for preview)
        vacancy = Vacancy.objects.get(pk=pk)
        
        # Check if user can view inactive vacancies
        if not vacancy.is_active and not request.user.is_staff:
            return render(request, 'vacancies/inactive.html', {'vacancy': vacancy})
        
        return render(request, 'vacancies/detail.html', {'vacancy': vacancy})
        
    except Vacancy.DoesNotExist:
        # Return 404 with helpful message
        return render(request, '404.html', {
            'message': 'Vacancy not found or has been removed.'
        }, status=404)


def get_vacancies(request):
    """API for homepage - simplified"""
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
    
    featured_list = []
    for v in featured:
        featured_list.append({
            'id': v.id,
            'title': v.title,
            'organization': v.organization,
            'location': v.location,
            'job_type': v.get_job_type_display(),
            'deadline': v.application_deadline.strftime('%b %d'),
            'days_left': v.days_remaining(),
        })
    
    recent_list = []
    for v in recent:
        recent_list.append({
            'id': v.id,
            'title': v.title,
            'organization': v.organization,
            'location': v.location,
            'job_type': v.get_job_type_display(),
        })
    
    return JsonResponse({
        'featured': featured_list,
        'recent': recent_list,
    })


# ==================== NOTICES ====================

def notice_list(request):
    """Simple notice list"""
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    
    notices = Notice.objects.filter(is_active=True)
    
    if search:
        notices = notices.filter(
            Q(title__icontains=search) |
            Q(organization__icontains=search) |
            Q(description__icontains=search)
        )
    
    if category:
        notices = notices.filter(category=category)
    
    return render(request, 'notices/list.html', {
        'notices': notices,
        'search': search,
        'category': category,
        'categories': Notice.CATEGORIES,
    })


def notice_detail(request, pk):
    """Notice detail view - Show even if not active"""
    try:
        # Get the notice (including inactive ones for preview)
        notice = Notice.objects.get(pk=pk)
        
        # Check if user can view inactive notices
        if not notice.is_active and not request.user.is_staff:
            return render(request, 'notices/inactive.html', {'notice': notice})
        
        return render(request, 'notices/detail.html', {'notice': notice})
        
    except Notice.DoesNotExist:
        # Return 404 with helpful message
        return render(request, '404.html', {
            'message': 'Notice not found or has been removed.'
        }, status=404)


def get_notices(request):
    """API for homepage - simplified"""
    # Important notices
    important = Notice.objects.filter(
        is_active=True,
        is_important=True
    )[:4]
    
    # Recent notices
    recent = Notice.objects.filter(is_active=True).order_by('-created_at')[:4]
    
    important_list = []
    for n in important:
        important_list.append({
            'id': n.id,
            'title': n.title,
            'description': n.description[:100] + '...' if len(n.description) > 100 else n.description,
            'organization': n.organization,
            'category': n.get_category_display(),
            'has_file': bool(n.attachment),
        })
    
    recent_list = []
    for n in recent:
        recent_list.append({
            'id': n.id,
            'title': n.title,
            'description': n.description[:80] + '...' if len(n.description) > 80 else n.description,
            'organization': n.organization,
        })
    
    return JsonResponse({
        'important': important_list,
        'recent': recent_list,
    })





# ==================== VACANCY UPLOAD ====================

@login_required
def upload_vacancy(request):
    """Simple vacancy upload form"""
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        if form.is_valid():
            vacancy = form.save()
            
            # Optional: Add success message
            messages.success(request, 'Vacancy posted successfully!')
            
            return redirect('vacancy_detail', pk=vacancy.id)
        else:
            # Return form with errors
            return render(request, 'vacancies/upload.html', {
                'form': form,
                'error': 'Please fix the errors below'
            })
    
    # GET request - show empty form
    form = VacancyForm()
    return render(request, 'vacancies/upload.html', {'form': form})


# ==================== NOTICE UPLOAD ====================

@login_required
def upload_notice(request):
    """Simple notice upload form"""
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save()
            
            messages.success(request, 'Notice posted successfully!')
            
            return redirect('notice_detail', pk=notice.id)
        else:
            return render(request, 'notices/upload.html', {
                'form': form,
                'error': 'Please fix the errors below'
            })
    
    form = NoticeForm()
    return render(request, 'notices/upload.html', {'form': form})


# ==================== AJAX UPLOAD (OPTIONAL) ====================

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
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


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
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})