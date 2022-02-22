from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


POSTS_PER_PAGE = 10


def get_page_context(queryset, request):
    paginator = Paginator(queryset, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'page_number': page_number,
        'page_obj': page_obj,
    }


def index(request):
    title = 'Последние обновления на сайте'
    context = {
        'title': title,
    }
    context.update(get_page_context(Post.objects.all(), request))
    return render(
        request,
        'posts/index.html',
        context
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    context = {
        'group': group,
    }
    context.update(get_page_context(group.posts.all(), request))
    return render(
        request,
        'posts/group_list.html',
        context
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_num = author.posts.count()
    following = request.user.is_authenticated and Follow.objects.filter(
            user=request.user,
            author=author
    ).exists()
    context = {
        'author': author,
        'posts_num': posts_num,
        'following': following,
    }
    context.update(get_page_context(author.posts.all(), request))
    return render(
        request,
        'posts/profile.html',
        context
    )


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post)
    posts_num = post.author.posts.count()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'posts_num': posts_num,
        'post_id': post_id,
        'form': form,
        'comments': comments,
    }
    return render(
        request,
        'posts/post_detail.html',
        context
    )


@login_required
def post_create(request):
    title = 'Новый пост'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    context = {
        'form': form,
        'title': title,
    }
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(
        request,
        'posts/create_post.html',
        context
    )


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    title = 'Редактировать пост'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
        'title': title,
    }
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(
        request,
        'posts/create_post.html',
        context
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    title = 'Поcты избранных авторов'
    context = {
        'title': title,
    }
    context.update(get_page_context(
        Post.objects.filter(author__following__user=request.user),
        request
    ))
    return render(
        request,
        'posts/follow.html',
        context
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(
        user=request.user,
        author=author
    )
    if follow.exists():
        follow.delete()
    return redirect('posts:profile', username=username)
