from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.


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






# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from publisher.models import BlogPost, Category

@login_required
def create_story(request, story_id=None):
    story = None
    if story_id:
        story = get_object_or_404(BlogPost, id=story_id, author=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        status = request.POST.get('status', 'DRAFT')
        action = request.POST.get('action', '')
        
        # Validate required fields for publishing
        if status == 'PUBLISHED':
            if not title:
                messages.error(request, 'Title is required for publishing')
                return redirect(request.path)
            if not content:
                messages.error(request, 'Content is required for publishing')
                return redirect(request.path)
        
        if story:
            # Update existing story
            story.title = title
            story.content = content
            story.category_id = request.POST.get('category')
            story.status = status
            
            if 'thumbnail' in request.FILES:
                story.thumbnail = request.FILES['thumbnail']
            
            # Set published_at if publishing and not already published
            if status == 'PUBLISHED' and not story.published_at:
                story.published_at = timezone.now()
            
            story.save()
            messages.success(request, f'Story updated and saved as {status.lower()}')
        else:
            # Create new story
            story = BlogPost.objects.create(
                title=title,
                content=content,
                category_id=request.POST.get('category'),
                status=status,
                author=request.user
            )
            
            if 'thumbnail' in request.FILES:
                story.thumbnail = request.FILES['thumbnail']
                story.save()
            
            # Set published_at if publishing
            if status == 'PUBLISHED':
                story.published_at = timezone.now()
                story.save()
            
            messages.success(request, f'Story created and saved as {status.lower()}')
        
        # Optional newsletter logic
        if action == 'publish':
            # Add newsletter sending logic here
            pass
            
        return redirect('story_list')
    
    categories = Category.objects.all()
    return render(request, 'management/create_story_page.html', {
        'story': story,
        'categories': categories
    })