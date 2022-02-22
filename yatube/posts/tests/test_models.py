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
        models = {
            post: expected_post_name,
            group: expected_group_name,
            comment: expected_comment_name,
        }
        for value, expected in models.items():
            with self.subTest(value=value):
                self.assertEqual(str(value), expected)
        self.assertEqual(self.follower.username, expected_follow_user_name)

    def test_verbose_name_post(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_verbose_name_group(self):
        group = PostModelTest.group
        self.assertEqual(
            group._meta.get_field('title').verbose_name, 'Группа'
        )

    def test_verbose_name_comment(self):
        comment = PostModelTest.comment
        self.assertEqual(
            comment._meta.get_field('text').verbose_name, 'Текст комментария'
        )

    def test_help_text_post(self):
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
            'image': 'Загрузите изображение с вашего компьютера',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

    def test_help_text_group(self):
        group = PostModelTest.group
        self.assertEqual(
            group._meta.get_field('title').help_text,
            'Группа, к которой будет относиться пост'
        )

    def test_help_text_comment(self):
        comment = PostModelTest.comment
        self.assertEqual(
            comment._meta.get_field('text').help_text,
            'Введите текст комментария'
        )
