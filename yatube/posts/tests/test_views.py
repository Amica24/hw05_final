import shutil
import tempfile
from itertools import islice

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, User, Follow
from ..forms import PostForm


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.user_other = User.objects.create_user(username='other')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.group_other = Group.objects.create(
            title='Другая тестовая группа',
            slug='different-slug',
            description='Другое тестовое описание',
        )
        cls.post_other = Post.objects.create(
            author=cls.user_other,
            text='Другой тестовый пост',
            group=cls.group_other,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user_non_author = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_non_author)
        self.authorized_author = Client()
        self.authorized_author.force_login(PostPagesTests.user)
        self.post_num = PostPagesTests.user.posts.count()

    def test_pages_uses_correct_template(self):
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.post.author.username}
            ):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:index'))
        first_post = response.context['page_obj'][1]
        self.assertEqual(first_post, self.post)
        self.assertEqual(response.context['title'],
                         'Последние обновления на сайте')

    def test_group_list_page_show_correct_context(self):
        response = (
            self.guest_client.get(reverse('posts:group_list',
                                          kwargs={'slug': self.group.slug}))
        )
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post, self.post)
        self.assertEqual(response.context['group'], self.post.group)

    def test_profile_page_show_correct_context(self):
        response = (
            self.guest_client.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.post.author.username}
                )
            )
        )
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post, self.post)
        self.assertEqual(
            response.context['author'].username, self.post.author.username
        )
        self.assertEqual(response.context['posts_num'], self.post_num)

    def test_post_detail_show_correct_context(self):
        response = (
            self.guest_client.get(reverse('posts:post_detail',
                                          kwargs={'post_id': self.post.id}))
        )
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(response.context['posts_num'], self.post_num)
        self.assertEqual(response.context['post_id'], self.post.id)

    def test_post_edit_show_correct_context(self):
        response = (
            self.authorized_author.get(
                reverse('posts:post_edit', kwargs={'post_id': self.post.id})
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(response.context['title'], 'Редактировать пост')
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIsInstance(response.context['is_edit'], bool)
        self.assertTrue(response.context['is_edit'])

    def test_post_create_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context['title'], 'Новый пост')
        self.assertIsInstance(response.context['form'], PostForm)

    def test_post_create_additional_check(self):
        form_data = {
            'text': 'Тестовый пост проверка формы',
            'group': self.post.group.pk,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        page_names = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.post.group.slug}),
            reverse('posts:profile', kwargs={'username': 'HasNoName'}),
        }
        for reverse_name in page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    response.context['page_obj'][0].text,
                    'Тестовый пост проверка формы'
                )
                self.assertEqual(
                    response.context['page_obj'][0].group.pk,
                    self.post.group.pk
                )

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_other.slug})
        )
        self.assertNotEqual(
            response.context['page_obj'][0].text,
            'Тестовый пост проверка формы'
        )
        self.assertNotEqual(
            response.context['page_obj'][0].group.pk,
            self.post.group.pk
        )

    def test_cache(self):
        cache.clear()
        post = Post.objects.create(
            author=self.user,
            text='Тест кеш пост',
        )
        response = self.guest_client.get(reverse('posts:index'))
        cache_with_post = response.content
        post.delete()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_with_post)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_with_post)

    def test_follow_for_authorized_user(self):
        follows_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user})
        )
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        follow = Follow.objects.get()
        self.assertEqual(follow.user, self.user_non_author)
        self.assertEqual(follow.author, self.user)

    def test_follow_for_non_authorized_user(self):
        follows_count = Follow.objects.count()
        self.guest_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user})
        )
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_unfollow_for_authorized_user(self):
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user})
        )
        follows_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user})
        )
        self.assertEqual(Follow.objects.count(), follows_count - 1)

    def test_follow_next_post(self):
        self.user_non_follower = User.objects.create_user(
            username='Notfollower'
        )
        Post.objects.create(
            author=self.user_non_follower,
            text='Тест подписки другой автор',
        )
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user})
        )
        Post.objects.create(
            author=self.user,
            text='Тест подписки',
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(
            response.context['page_obj'][0].text,
            'Тест подписки'
        )
        self.authorized_author.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_non_follower})
        )
        response = self.authorized_author.get(
            reverse('posts:follow_index')
        )
        self.assertNotEqual(
            response.context['page_obj'][0].text,
            'Тест подписки'
        )

    def test_follow_auth(self):
        follows_count = Follow.objects.count()
        self.authorized_author.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user})
        )
        self.assertEqual(Follow.objects.count(), follows_count)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        batch_size = 13
        posts = (Post(
            text='Тестовый пост номер %s' % i,
            author=cls.user,
            group=cls.group
        ) for i in range(batch_size))
        batch = list(islice(posts, batch_size))
        Post.objects.bulk_create(batch, batch_size)

    def setUp(self):
        self.guest_client = Client()

    def test_pages_has_paginator_contains_required_records(self):
        page_names = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        }

        for reverse_name in page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.guest_client.get(reverse_name, {'page': 2})
                self.assertEqual(len(response.context['page_obj']), 3)
