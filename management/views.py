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

def write_article_page(request):
	return render(request, 'management/write_article_page.html')