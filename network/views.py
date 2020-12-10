import json
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django import forms
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse
import datetime
from .models import User, Post, Like


class Entry(forms.Form):
    content = forms.CharField(label=False, widget=forms.Textarea(
        attrs={"rows": 5, "cols": 40, "size": 500, "class": "post-content"}))


@csrf_protect
def index(request):
    if request.method == "POST":
        # Collect form data, add new post to database
        form = Entry(request.POST)
        if form.is_valid():
            # Retrieve form data
            content = form.cleaned_data["content"]

            # Get User object for current user
            user = request.user

            # Create new post model instance
            post = Post.objects.create(
                content=content,
                submitter=user,
            )
            post.save()

            # Redirect to index page
            return HttpResponseRedirect(reverse("index"))

    elif request.method == "GET":
        # Query all posts to show most recent posts at top of page
        all_posts = Post.objects.order_by("posted_on").reverse()

        # Call function to render pagination
        page = render_pagination(request, all_posts)

        # Check if user is authenticated, if so, create new post form
        if request.user.is_authenticated:
            new_entry_form = Entry()
            show_entry_form = True
            # Render view for authenticated user
            return render(request, "network/index.html", {
                "page": page, "header": "All Posts:",
                "new_entry_form": new_entry_form,
                "show_entry_form": show_entry_form
            })
        else:
            # Render view for unauthenticated user
            return render(request, "network/index.html", {
                "page": page, "header": "All Posts"
            })


def profile(request, user_id):
    # Create flag signaling for visibility of profile attributes
    show_profile_attributes = True

    # Get User object for current profile author
    author = User.objects.get(id=user_id)

    # Query for all posts by the current author
    all_posts = Post.objects.order_by("posted_on")
    profile_posts = all_posts.filter(submitter=user_id)
    profile_posts_ordered = profile_posts.order_by("posted_on").reverse()

    # Query author instance for number of users following and followed
    following_count = author.following.all().count()
    follower_count = author.followers.all().count()

    # Encapsulate follow function so only accessible to authenticated users
    if request.user.is_authenticated:

        # Get User object for current user
        user = request.user

        # Query to determine if current user follows profile author
        follow_query = User.objects.filter(following=user_id)
        match_query = follow_query.filter(id=user.id)

        # When follow button is clicked perform proper database modification
        if request.method == "POST":
            if match_query.exists():
                user.following.remove(user_id)
            else:
                user.following.add(user_id)
        # Create flag to display correct button on profile page
        if match_query.exists():
            follow_status = "Followed"
        else:
            follow_status = "Not Followed"

        # Create new post form
        new_entry_form = Entry()

        # Perform pagination
        page = render_pagination(request, profile_posts_ordered)

        # Render view for authenticated user
        return render(request, "network/index.html", {
            "author": author, "following": following_count,
            "followers": follower_count, "follow_status": follow_status,
            "header": author, "page": page,
            "show_profile_attributes": show_profile_attributes
        })
    else:
        # Render view for unauthenticated user
        page = render_pagination(request, profile_posts_ordered)
        return render(request, "network/index.html", {
            "author": author, "following": following_count,
            "followers": follower_count, "header": author, "page": page,
            "show_profile_attributes": show_profile_attributes
        })


@login_required
def edit_post(request, post_id):
    # Editing a post must be via PUT
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)

    # Retrieve instance of selected post
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)

    # Load data from json fetch request
    data = json.loads(request.body)
    # If fetch request sends post content, update database
    if data.get("content") is not None:
        post.content = data["content"]
    post.save()

    # Redirect to index page.
    return JsonResponse({"Success": "Post Edited Successfully."}, status=201)


@login_required
@csrf_protect
def like_post(request):
    # Adding a like must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    # Get contents of post
    data = json.loads(request.body)
    post_id = data.get("post", "")
    post = Post.objects.get(id=post_id)

    # Get User object for current user
    user = request.user

    # Filter to determine if current user already likes this post
    likes_on_post = Like.objects.filter(post=post)
    current_like = likes_on_post.filter(user=user)

    # If user likes this post, remove like. Else, add like.
    if current_like:
        current_like.delete()
    else:
        like = Like(
            post=post,
            user=user
        )
        like.save()

    # Count number of total likes on post
    new_like_count = likes_on_post.count()

    # Pass new number of total likes as JsonResponse
    data = {
        "newCount": new_like_count
    }
    return JsonResponse(data, status=201)


def render_pagination(request, posts):

    # Set page number, default to 1
    page_num = request.GET.get("page", 1)

    # Set maximum number of posts per page
    paginator = Paginator(posts, per_page=10)
    page = paginator.page(page_num)

    # Return paginated file
    return page


@login_required
def following(request):

    # Get User object for current user
    user = request.user

    # Query for users who the current user is following
    following_query = User.objects.filter(followers=user.id)

    # Query for posts submitted by users that the current user follows
    following_posts = Post.objects.filter(submitter__in=following_query)

    # Orders posts to display most recent posts at the top of the page
    following_posts_reverse = following_posts.order_by("posted_on").reverse()

    # Render pagination
    page = render_pagination(request, following_posts_reverse)

    # Create new post form
    new_entry_form = Entry()

    return render(request, "network/index.html", {
        "page": page, "header": "Following:",
        "new_entry_form": new_entry_form
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
