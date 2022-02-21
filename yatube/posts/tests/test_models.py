from django.test import TestCase

from ..models import Group, Post, User, Comment, Follow


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )
        cls.follower = User.objects.create_user(username='follower')
        cls.comment = Comment.objects.create(
            author=cls.follower,
            post=cls.post,
            text='Тестовый комментарий',
        )
        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.user,
        )

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        follow = PostModelTest.follow
        expected_group_name = group.title
        expected_post_name = post.text[:15]
        expected_comment_name = comment.text
        expected_follow_user_name = follow.user.username
        self.assertEqual(expected_group_name, str(group))
        self.assertEqual(expected_post_name, str(post))
        self.assertEqual(expected_comment_name, str(comment))
        self.assertEqual(expected_follow_user_name, self.follower.username)

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
