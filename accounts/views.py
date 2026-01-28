from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.text import Truncator

from .models import SiteInfo, TeamMember, User

from django.contrib import messages
from django.utils import timezone




# views.py - Add these functions


from django.contrib.auth.forms import UserCreationForm, AuthenticationForm




# Profile View
@login_required
def profile_view(request):
    return render(request, 'auth/profile.html', {'user': request.user})

# Saved Stories View
@login_required
def saved_stories_view(request):
    # Assuming you have a 'saved_by' field in your Story model
    # or a separate SavedStory model
    saved_stories = Story.objects.filter(saved_by=request.user).order_by('-created_at')
    # OR if you have a ManyToMany relationship
    # saved_stories = request.user.saved_stories.all()
    
    return render(request, 'auth/saved_stories.html', {'saved_stories': saved_stories})

# Save Story Action
@login_required
def save_story_view(request, story_id):
    if request.method == 'POST':
        try:
            story = Story.objects.get(id=story_id)
            # Toggle save status
            if request.user in story.saved_by.all():
                story.saved_by.remove(request.user)
                saved = False
            else:
                story.saved_by.add(request.user)
                saved = True
            
            return JsonResponse({'success': True, 'saved': saved})
        except Story.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Story not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})



def about_page(request):
    """About us page"""
    site_info = get_object_or_404(SiteInfo, id=1)
    
    # Get active team members (max 5)
    team_members = TeamMember.objects.filter(
        is_active=True,
        user__is_active=True
    ).order_by('display_order')[:5]
    
    return render(request, 'about/about.html', {
        'site_info': site_info,
        'team_members': team_members,
    })


def contact_page(request):
    """Contact page"""
    site_info = get_object_or_404(SiteInfo, id=1)
    
    return render(request, 'about/contact.html', {
        'site_info': site_info,
    })


@staff_member_required
def edit_about(request):
    """Edit about page (staff only)"""
    site_info = get_object_or_404(SiteInfo, id=1)
    
    if request.method == 'POST':
        site_info.about_us = request.POST.get('about_us', '')
        site_info.mission = request.POST.get('mission', '')
        site_info.vision = request.POST.get('vision', '')
        site_info.contact_email = request.POST.get('contact_email', '')
        site_info.contact_phone = request.POST.get('contact_phone', '')
        site_info.address = request.POST.get('address', '')
        site_info.facebook_url = request.POST.get('facebook_url', '')
        site_info.twitter_url = request.POST.get('twitter_url', '')
        site_info.linkedin_url = request.POST.get('linkedin_url', '')
        site_info.save()
        
        return JsonResponse({
            'success': True,
            'message': 'About page updated successfully!'
        })
    
    return render(request, 'about/edit.html', {
        'site_info': site_info,
    })


@staff_member_required
def edit_team_member(request, user_id):
    """Edit team member profile (staff only)"""
    team_member = get_object_or_404(TeamMember, user_id=user_id)
    
    if request.method == 'POST':
        team_member.position = request.POST.get('position', '')
        team_member.bio = request.POST.get('bio', '')
        team_member.twitter_url = request.POST.get('twitter_url', '')
        team_member.linkedin_url = request.POST.get('linkedin_url', '')
        team_member.display_order = request.POST.get('display_order', 0)
        team_member.is_active = request.POST.get('is_active') == 'true'
        team_member.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Team member updated successfully!'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    })


def team_member_detail(request, username):
    """View team member profile"""
    user = get_object_or_404(User, username=username, is_active=True)
    team_member = get_object_or_404(TeamMember, user=user, is_active=True)
    
    return render(request, 'about/team_member.html', {
        'team_member': team_member,
    })




# ==================== SITE INFO ====================

@staff_member_required
def manage_site_info(request):
    """Manage site information (About, Contact, etc.)"""
    # Get or create site info
    site_info, created = SiteInfo.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        # Update site info
        site_info.about_us = request.POST.get('about_us', '')
        site_info.mission = request.POST.get('mission', '')
        site_info.vision = request.POST.get('vision', '')
        
        # Contact info
        site_info.contact_email = request.POST.get('contact_email', '')
        site_info.contact_phone = request.POST.get('contact_phone', '')
        site_info.address = request.POST.get('address', '')
        
        # Social media
        site_info.facebook_url = request.POST.get('facebook_url', '')
        site_info.twitter_url = request.POST.get('twitter_url', '')
        site_info.linkedin_url = request.POST.get('linkedin_url', '')
        
        site_info.save()
        
        messages.success(request, 'Site information updated successfully!')
        return redirect('manage_site_info')
    
    return render(request, 'about/manage_site.html', {
        'site_info': site_info,
    })


# ==================== TEAM MEMBERS ====================

@staff_member_required
def manage_team(request):
    """Manage team members"""
    # Get active team members (max 5)
    team_members = TeamMember.objects.all().order_by('display_order')
    
    # Get staff users who don't have team profiles yet
    staff_users = User.objects.filter(
        is_staff=True,
        is_active=True
    ).exclude(team_profile__isnull=False)
    
    return render(request, 'about/manage_team.html', {
        'team_members': team_members,
        'staff_users': staff_users,
    })


@staff_member_required
def add_team_member(request):
    """Add new team member"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        position = request.POST.get('position', '')
        
        if not user_id or not position:
            messages.error(request, 'Please select a user and enter a position')
            return redirect('manage_team')
        
        try:
            user = User.objects.get(id=user_id, is_staff=True, is_active=True)
            
            # Check if already a team member
            if hasattr(user, 'team_profile'):
                messages.error(request, f'{user.get_full_name()} is already a team member')
                return redirect('manage_team')
            
            # Create team member
            team_member = TeamMember.objects.create(
                user=user,
                position=position,
                bio=request.POST.get('bio', ''),
                twitter_url=request.POST.get('twitter_url', ''),
                linkedin_url=request.POST.get('linkedin_url', ''),
                display_order=request.POST.get('display_order', 0) or 0,
                is_active=request.POST.get('is_active') == 'on'
            )
            
            messages.success(request, f'{user.get_full_name()} added to team successfully!')
            return redirect('manage_team')
            
        except User.DoesNotExist:
            messages.error(request, 'Selected user not found')
            return redirect('manage_team')
    
    return redirect('manage_team')


@staff_member_required
def edit_team_member(request, user_id):
    """Edit team member"""
    team_member = get_object_or_404(TeamMember, user_id=user_id)
    
    if request.method == 'POST':
        team_member.position = request.POST.get('position', '')
        team_member.bio = request.POST.get('bio', '')
        team_member.twitter_url = request.POST.get('twitter_url', '')
        team_member.linkedin_url = request.POST.get('linkedin_url', '')
        team_member.display_order = request.POST.get('display_order', 0) or 0
        team_member.is_active = request.POST.get('is_active') == 'on'
        team_member.save()
        
        messages.success(request, 'Team member updated successfully!')
        return redirect('manage_team')
    
    return render(request, 'about/edit_team.html', {
        'team_member': team_member,
    })


@staff_member_required
def delete_team_member(request, user_id):
    """Delete team member"""
    team_member = get_object_or_404(TeamMember, user_id=user_id)
    user_name = team_member.user.get_full_name()
    team_member.delete()
    
    messages.success(request, f'{user_name} removed from team successfully!')
    return redirect('manage_team')