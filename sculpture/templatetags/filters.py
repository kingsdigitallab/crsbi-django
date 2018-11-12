from django import template

from sculpture.models.site_image import SiteImage
from sculpture.models.site import Site
from mezzanine.blog.models import BlogPost

register = template.Library()

@register.filter(is_safe=True)
def islist (value):
    return isinstance(value, list)


@register.filter()
def getLatestImages(value):
    return SiteImage.objects.all().filter(site__status__name="Accepted").order_by("-id")[0:6]
    

@register.filter()
def getFiveLatestImages(value):
    return SiteImage.objects.all().filter(site__status__name="Accepted").order_by("-id")[0:5]
    
    
@register.filter()
def getFullSiteList(request):
    pg = 1
    try:
        pg = int(request.GET['page'])
    except:
        pass
        
    return Site.objects.all().filter(status__name="Accepted").order_by("name")[(pg-1) * 20: pg * 20]


@register.filter()
def getFullSiteListHasPrev(request):
    pg = 1
    try:
        pg = int(request.GET['page'])
    except:
        pass
        
    if pg > 1:
        return pg - 1
    else:
        return 0
    
@register.filter()
def getFullSiteListHasNext(request):
    pg = 1
    try:
        pg = int(request.GET['page'])
    except:
        pass
        
    if Site.objects.all().filter(status__name="Accepted").count() > (pg * 20):
        return pg + 1
    else:
        return 0
        
@register.filter()
def getFullImageList(request):
    pg = 1
    try:
        pg = int(request.GET['page'])
    except:
        pass
        
    return SiteImage.objects.all().filter(site__status__name="Accepted")[(pg-1) * 20: pg * 20]


@register.filter()
def getFullImageListHasPrev(request):
    pg = 1
    try:
        pg = int(request.GET['page'])
    except:
        pass
        
    if pg > 1:
        return pg - 1
    else:
        return 0
    
@register.filter()
def getFullImageListHasNext(request):
    pg = 1
    try:
        pg = int(request.GET['page'])
    except:
        pass
        
    if SiteImage.objects.all().filter(site__status__name="Accepted").count() > (pg * 20):
        return pg + 1
    else:
        return 0
    
@register.filter(is_safe=True)
def stripPage(val):
    if "&page" in val:
        return val.split("&page")[0]
    else:
        return val.split("?page")[0]
        
    

@register.filter(is_safe=True)
def imageToSite(val):
    return val.replace("/search/image/", "/search/")
    

@register.filter(is_safe=True)
def siteToImage(val):
    return val.replace("/search/", "/search/image/")
    

@register.filter()
def getLastBlogPosts(request):
    # Only published posts
    posts = BlogPost.objects.select_related().filter(status=2).order_by("-id")
    if posts.count() < 3:
        return posts
    else:
        return posts[0:3]
        

@register.filter()
def getStickyBlogPosts(request):
    # Only published posts
    posts = BlogPost.objects.select_related().filter(status=2).order_by("-id").filter(categories=1)
    if posts.count() < 3:
        return posts
    else:
        return posts[0:3]
        
@register.filter()
def getNotStickyBlogPosts(request):
    # Only published posts
    posts = BlogPost.objects.select_related().filter(status=2).order_by("-id").exclude(categories=1)
    if posts.count() < 3:
        return posts
    else:
        return posts[0:3]

        
@register.filter()
def isIconView(request):
    try:
        if request.COOKIES['view_options'] == "grid":
            return True
        else:
            return False
    except:
        return False
        
@register.filter()
def parseSlideshow(value):
    return value.replace("**slideshow**", "<div id='slides'></div>")
