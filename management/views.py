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



def management_story_list_page(request):
	return render(request, 'management/management_story_list_page.html')


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




