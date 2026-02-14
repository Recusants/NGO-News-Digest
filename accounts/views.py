import json
import secrets
from datetime import timedelta

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .forms import CustomAuthenticationForm, CustomPasswordChangeForm, UserProfileForm, TeamMemberProfileForm
from .models import User, TeamMember, PasswordResetCode


# ---------------------------------------------------------
# views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import User, TeamMember
from .forms import UserForm, UserProfileForm, TeamMemberForm

def is_admin(user):
    """Check if user has admin role"""
    return user.is_authenticated and user.roles == 'admin'

@login_required
@user_passes_test(is_admin)
def user_list(request):
    """List all users (admin only)"""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(roles=role_filter)
    
    # Sort by creation date (newest first)
    users = users.order_by('-created_at')
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'user_roles': dict(User.ROLES),
    }
    return render(request, 'auth/user_list.html', context)

@login_required
@user_passes_test(is_admin)
def user_create(request):
    """Create new user (admin only)"""
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.created_by = request.user
            user.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('user_list')
    else:
        form = UserForm()
    
    context = {'form': form}
    return render(request, 'auth/user_form.html', context)

@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    """Edit user (admin only)"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'is_edit': True,
    }
    return render(request, 'auth/user_form.html', context)

@login_required
@user_passes_test(is_admin)
def user_toggle_active(request, pk):
    """Enable/disable user (admin only)"""
    user = get_object_or_404(User, pk=pk)
    
    if user == request.user:
        messages.error(request, 'You cannot disable your own account!')
        return redirect('user_list')
    
    user.is_active = not user.is_active
    user.save()
    
    action = 'enabled' if user.is_active else 'disabled'
    messages.success(request, f'User {user.username} has been {action}.')
    return redirect('user_list')

@login_required
@user_passes_test(is_admin)
def user_delete(request, pk):
    """Delete user (admin only)"""
    user = get_object_or_404(User, pk=pk)
    
    if user == request.user:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} has been deleted.')
        return redirect('user_list')
    
    context = {'user': user}
    return render(request, 'management/users/user_confirm_delete.html', context)

@login_required
def user_profile(request):
    """User profile view (accessible by all logged-in users)"""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=user)
    
    try:
        team_profile = user.team_profile
    except TeamMember.DoesNotExist:
        team_profile = None
    
    context = {
        'form': form,
        'team_profile': team_profile,
        'user': user,
    }
    return render(request, 'auth/profile.html', context)

@login_required
def team_profile_edit(request):
    """Edit team profile (if exists)"""
    user = request.user
    
    try:
        team_profile = user.team_profile
    except TeamMember.DoesNotExist:
        team_profile = None
    
    if request.method == 'POST':
        if team_profile:
            form = TeamMemberForm(request.POST, request.FILES, instance=team_profile)
        else:
            form = TeamMemberForm(request.POST, request.FILES)
        
        if form.is_valid():
            team_profile = form.save(commit=False)
            team_profile.user = user
            team_profile.save()
            messages.success(request, 'Team profile updated successfully!')
            return redirect('user_profile')
    else:
        if team_profile:
            form = TeamMemberForm(instance=team_profile)
        else:
            form = TeamMemberForm()
    
    context = {
        'form': form,
        'team_profile': team_profile,
    }
    return render(request, 'management/users/team_profile_form.html', context)




















































































class LoginView(View):
    template_name = 'auth/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('user_profile')
        return render(request, self.template_name, {
            'form': CustomAuthenticationForm()
        })

    def post(self, request):
        tab = request.POST.get('tab', 'login')

        if tab == 'login':
            return self.handle_login(request)

        if tab == 'password_reset':
            return self.handle_password_reset(request)

        return redirect('login')

    def handle_login(self, request):
        form = CustomAuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if not request.POST.get('remember_me'):
                request.session.set_expiry(0)

            messages.success(request, f'Welcome back, {user.username}!')
            return redirect(request.POST.get('next', 'user_profile'))

        messages.error(request, 'Invalid username or password.')
        return render(request, self.template_name, {'form': form})

    def handle_password_reset(self, request):
        if not request.session.get('reset_verified'):
            messages.error(request, 'Password reset not verified.')
            return redirect('login')

        user_id = request.session.get('reset_user_id')
        if not user_id:
            messages.error(request, 'Reset session expired.')
            return redirect('login')

        password1 = request.POST.get('new_password1')
        password2 = request.POST.get('new_password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('login')

        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect('login')

        user = User.objects.get(id=user_id)
        user.set_password(password1)
        user.save()

        request.session.flush()
        messages.success(request, 'Password reset successful. Please log in.')
        return redirect('login')


# ============================
# AJAX PASSWORD RESET ENDPOINTS
# ============================

def send_reset_code(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})

    data = json.loads(request.body)
    email = data.get('email')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'No user with that email.'})

    code = str(secrets.randbelow(1000000)).zfill(6)

    PasswordResetCode.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=10)
    )

    request.session['reset_user_id'] = user.id
    request.session['reset_verified'] = False

    try:
        send_mail(
            'Password Reset Code',
            f'Your password reset code is: {code}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )
    except Exception:
        # DEV fallback
        return JsonResponse({
            'success': True,
            'message': 'Email not configured.',
            'code': code
        })

    return JsonResponse({'success': True, 'message': 'Code sent successfully.'})


def verify_reset_code(request):
    if request.method != 'POST':
        return JsonResponse({'success': False})

    data = json.loads(request.body)
    code = data.get('code')
    user_id = request.session.get('reset_user_id')

    if not code or not user_id:
        return JsonResponse({'success': False, 'message': 'Invalid session.'})

    reset_code = PasswordResetCode.objects.filter(
        user_id=user_id,
        code=code,
        is_used=False,
        expires_at__gt=timezone.now()
    ).first()

    if not reset_code:
        return JsonResponse({'success': False, 'message': 'Invalid or expired code.'})

    reset_code.is_used = True
    reset_code.save()
    request.session['reset_verified'] = True

    return JsonResponse({'success': True, 'message': 'Code verified.'})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')



