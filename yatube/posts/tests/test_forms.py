from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group, User, Comment


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(PostCreateFormTests.user)

    def test_post_create_valid_form(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост проверка формы',
            'group': self.post.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': 'HasNoName'}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'HasNoName'})
        )
        self.assertEqual(
            response.context['page_obj'][0].text,
            form_data['text']
        )
        self.assertEqual(
            response.context['page_obj'][0].group.pk,
            form_data['group']
        )
        self.assertEqual(response.context['author'].username, 'HasNoName')
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост проверка формы',
                group=self.post.group.pk
            ).exists()
        )

    def test_post_create_form_for_unauthorized_user(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост проверка формы',
            'group': self.post.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый пост проверка формы',
                group=self.post.group.pk
            ).exists()
        )

    def test_post_edit_valid_form(self):
        form_data = {
            'text': 'Редактированный тестовый пост',
            'group': self.post.group.pk,
        }
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        response = self.authorized_author.get(
            reverse('posts:profile', kwargs={'username': 'auth'}))
        self.assertEqual(
            response.context['page_obj'][0].text,
            form_data['text']
        )
        self.assertEqual(
            response.context['page_obj'][0].group.pk,
            form_data['group']
        )
        self.assertEqual(response.context['author'].username, 'auth')
        self.assertTrue(
            Post.objects.filter(
                text='Редактированный тестовый пост',
                group=self.post.group.pk
            ).exists()
        )
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый пост',
                group=self.post.group.pk
            ).exists()
        )

    def test_post_edit_form_for_non_author(self):
        form_data = {
            'text': 'Редактированный тестовый пост',
            'group': self.post.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        self.assertFalse(
            Post.objects.filter(
                text='Редактированный тестовый пост',
                group=self.post.group.pk
            ).exists()
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                group=self.post.group.pk
            ).exists()
        )

    def test_post_edit_form_for_unauthorized_user(self):
        form_data = {
            'text': 'Редактированный тестовый пост',
            'group': self.post.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )
        self.assertFalse(
            Post.objects.filter(
                text='Редактированный тестовый пост',
                group=self.post.group.pk
            ).exists()
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                group=self.post.group.pk
            ).exists()
        )

    def test_comment_valid_form(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий проверка формы',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            response.context['comments'][0].text,
            form_data['text']
        )
        self.assertEqual(
            response.context['comments'][0].author.username,
            'HasNoName'
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий проверка формы'
            ).exists()
        )

    def test_validaiton_fail(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': '',
            'group': self.post.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFormError(response, 'form', "text", 'Обязательное поле.')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text='',
                group=self.post.group.pk
            ).exists()
        )
