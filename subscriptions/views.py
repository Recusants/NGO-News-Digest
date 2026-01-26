from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
import uuid
import re
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
import csv
import threading

from accounts.models import Subscriber

# Email sending in background thread
class EmailThread(threading.Thread):
    def __init__(self, subject, plain_message, html_message, recipient_list):
        self.subject = subject
        self.plain_message = plain_message
        self.html_message = html_message
        self.recipient_list = recipient_list
        threading.Thread.__init__(self)

    def run(self):
        try:
            email = EmailMultiAlternatives(
                subject=self.subject,
                body=self.plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=self.recipient_list,
            )
            if self.html_message:
                email.attach_alternative(self.html_message, "text/html")
            email.send()
        except Exception as e:
            print(f"Error sending email: {e}")


def send_email_in_background(subject, plain_message, html_message, recipient_list):
    """Send email in background thread"""
    EmailThread(subject, plain_message, html_message, recipient_list).start()


def subscribe_page(request):
    """Render subscription page"""
    return render(request, 'subscriptions/subscribe.html')


def unsubscribe_page(request):
    """Render unsubscribe page"""
    return render(request, 'subscriptions/unsubscribe.html')

def subscription_result_page(request):
    return render(request, 'subscriptions/subscription_result_page.html')


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


def subscribe(request):
    """
    Handle newsletter subscription with verification link
    """
    if request.method != 'POST':
        return JsonResponse({'custome_status': "Error", 'message': 'Method not allowed'}, status=405)
    
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip().lower()
    
    # Validation
    if not name:
        return JsonResponse({'custome_status': "Error", 'message': 'Name is required'})
    
    if not email:
        return JsonResponse({'custome_status': "Error", 'message': 'Email is required'})
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return JsonResponse({'custome_status': "Error", 'message': 'Invalid email format'})
    
    verification_token = str(uuid.uuid4())
    
    already_exist = Subscriber.objects.filter(email=email)
    if already_exist:
        subscriber = already_exist[0]
        subscriber.name = name
        subscriber.verification_token = verification_token
        subscriber.is_verified = False
        subscriber.is_active = False
        subscriber.save()
    else:
        new_subscriber = Subscriber()
        new_subscriber.email = email
        new_subscriber.name = name
        new_subscriber.verification_token = verification_token
        new_subscriber.is_verified = False
        new_subscriber.is_active = False
        new_subscriber.save()
    
    verification_url = request.build_absolute_uri(
        f'/subscriptions/verify/{verification_token}/'
    )
    
    try:
        send_mail(
            subject='✅ Confirm Your Newsletter Subscription',
            message=f"""Hello {name},

Thank you for subscribing to our newsletter!

Please click the link below to confirm:
{verification_url}

Best regards,
Newsletter Team""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        return JsonResponse({
            'title': "Success",
            'message': f'Failed to send email: {e}',
            'icon': "success",
        })

    
    return JsonResponse({
        'title': "Success",
        'message': f'Thank you {name}! Please check your email ({email}) for verification.',
        'icon': "success",
    })


def verify_email(request, token):
    """Verify email using token"""
    try:
        subscriber = Subscriber.objects.get(verification_token=token)
        
        if subscriber.is_verified:
            return render(request, 'subscriptions/verification_result.html', {
                'success': True,
                'title': 'Already Verified',
                'message': f'Email {subscriber.email} is already verified.',
                'email': subscriber.email
            })
        
        subscriber.is_verified = True
        subscriber.is_active = True
        subscriber.verified_at = timezone.now()
        subscriber.save()
        
        return render(request, 'subscriptions/verification_result.html', {
            'success': True,
            'title': 'Email Verified Successfully!',
            'message': f'Your email has been verified successfully!',
            'email': subscriber.email
        })
        
    except Subscriber.DoesNotExist:
        return render(request, 'subscriptions/verification_result.html', {
            'success': False,
            'title': 'Invalid Token',
            'message': 'Invalid verification token.'
        })
    except Exception as e:
        return render(request, 'subscriptions/verification_result.html', {
            'success': False,
            'title': 'Error',
            'message': f'Server error. Please try again.'
        })


def unsubscribe(request):
    """
    Handle newsletter unsubscription
    """
    email = request.GET.get('email', '').strip().lower()
    
    if not email:
        return JsonResponse({'custome_status': "Error", 'message': 'Email is required'})
    
    already_exist = Subscriber.objects.filter(email=email)
    if already_exist:
        subscriber = already_exist[0]
        subscriber.is_active = False
        subscriber.save()
        return JsonResponse({
            'custome_status': "",
            'message': f'Email {email} has been unsubscribed successfully!'
        })
    else:
        return JsonResponse({
            'custome_status': "",
            'message': f'Email {email} was not found in our subscription list.'
        })


def get_subscriber_details(request):
    """Get subscriber details"""
    subscriber_id = request.GET.get('subscriber_id')
    subscriber = Subscriber.objects.get(id=int(subscriber_id))
    
    email = subscriber.email
    name = subscriber.name
    is_verified = subscriber.is_verified
    is_active = subscriber.is_active
    subscribed_at = str(subscriber.subscribed_at)[:10] if subscriber.subscribed_at else ""
    verified_at = str(subscriber.verified_at)[:10] if subscriber.verified_at else ""
    
    if subscriber.is_verified == True:
        verification_status = "True"
    else:
        verification_status = "False"
    
    if subscriber.is_active == True:
        active_status = "True"
    else:
        active_status = "False"
    
    details = {
        "email": email,
        "name": name,
        "verification_status": verification_status,
        "active_status": active_status,
        "subscribed_at": subscribed_at,
        "verified_at": verified_at
    }
    return JsonResponse({'custome_status': "", 'details': details})


def update_subscriber(request):
    """Update subscriber information"""
    subscriber_id = request.GET.get('subscriber_id')
    subscriber = Subscriber.objects.get(id=int(subscriber_id))
    
    name = request.GET.get('name')
    email = request.GET.get('email')
    is_verified = request.GET.get('is_verified')
    is_active = request.GET.get('is_active')
    
    already_exist = Subscriber.objects.filter(email=email)
    if already_exist:
        if already_exist[0].id != int(subscriber_id):
            return JsonResponse({
                'custome_status': "Error",
                'message': "Error, a subscriber with the exact email already exists in the system"
            })
    
    old_subscriber = subscriber
    old_subscriber.name = name
    old_subscriber.email = email
    
    if is_verified == "True":
        old_subscriber.is_verified = True
        old_subscriber.verified_at = timezone.now()
    else:
        old_subscriber.is_verified = False
        old_subscriber.verified_at = None
    
    if is_active == "True":
        old_subscriber.is_active = True
    else:
        old_subscriber.is_active = False
    
    old_subscriber.save()
    
    return JsonResponse({
        'custome_status': "",
        'message': "Subscriber updated successfully!"
    })