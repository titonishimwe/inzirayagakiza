from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, SimpleTestCase, TestCase

from core.models import Question, QuestionCategory
from core.utils import youtube_embed_url, youtube_video_id, youtube_watch_url

User = get_user_model()


class YouTubeUrlTests(SimpleTestCase):
    def test_watch_url(self):
        self.assertEqual(
            youtube_video_id('https://www.youtube.com/watch?v=9bZkp7q19f0'),
            '9bZkp7q19f0',
        )

    def test_short_url(self):
        self.assertEqual(
            youtube_video_id('https://youtu.be/9bZkp7q19f0'),
            '9bZkp7q19f0',
        )

    def test_shorts_url(self):
        self.assertEqual(
            youtube_video_id('https://www.youtube.com/shorts/9bZkp7q19f0'),
            '9bZkp7q19f0',
        )

    def test_embed_url(self):
        self.assertEqual(
            youtube_video_id('https://www.youtube.com/embed/9bZkp7q19f0'),
            '9bZkp7q19f0',
        )

    def test_channel_url_invalid(self):
        self.assertIsNone(
            youtube_video_id('https://www.youtube.com/@INZIRAYUBUGINGOTV/videos'),
        )

    def test_watch_normalization(self):
        self.assertEqual(
            youtube_watch_url('https://youtu.be/9bZkp7q19f0?t=10'),
            'https://www.youtube.com/watch?v=9bZkp7q19f0',
        )

    def test_embed_build(self):
        self.assertIn(
            '9bZkp7q19f0',
            youtube_embed_url('https://www.youtube.com/watch?v=9bZkp7q19f0', autoplay=True),
        )


class PublicPageSmokeTests(TestCase):
    """GET public routes — expect 200 (or 404 only when no matching content)."""

    PUBLIC_URLS = [
        '/',
        '/youtube/',
        '/audio/',
        '/pdf-content/',
        '/slides/',
        '/sermon/',
        '/resources/',
        '/qa/',
        '/get-in-touch/',
        '/search/',
        '/search/?q=faith',
        '/videos/',
        '/appointment/',
    ]

    def test_public_pages_load(self):
        client = Client()
        for path in self.PUBLIC_URLS:
            with self.subTest(path=path):
                response = client.get(path)
                self.assertIn(
                    response.status_code,
                    (200, 301, 302),
                    msg=f'{path} returned {response.status_code}',
                )

    def test_permanent_redirects(self):
        client = Client()
        r = client.get('/videos/')
        self.assertEqual(r.status_code, 301)
        self.assertIn('/youtube/', r['Location'])

        r = client.get('/appointment/')
        self.assertEqual(r.status_code, 301)
        self.assertIn('/get-in-touch/', r['Location'])

    def test_qa_detail_public_question(self):
        cat = QuestionCategory.objects.create(name='Faith', slug='faith')
        q = Question.objects.create(
            asker_name='Test',
            asker_email='test@example.com',
            question_text='What is grace?',
            answer_text='By faith.',
            status=Question.Status.ANSWERED,
            is_public=True,
            category=cat,
        )
        response = Client().get(f'/qa/{q.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_topic_hub_loads(self):
        QuestionCategory.objects.create(name='Prayer', slug='prayer')
        response = Client().get('/topics/prayer/')
        self.assertEqual(response.status_code, 200)


class DashboardSmokeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='pastor_test', password='testpass123')
        group, _ = Group.objects.get_or_create(name='Pastor')
        self.user.groups.add(group)

    DASHBOARD_URLS = [
        '/dashboard/',
        '/dashboard/questions/',
        '/dashboard/resources/',
        '/dashboard/messages/',
        '/dashboard/contact-messages/',
        '/dashboard/site-content/',
        '/dashboard/categories/',
        '/dashboard/account/',
    ]

    DASHBOARD_REDIRECTS = {
        '/dashboard/notifications/': '/dashboard/messages/',
        '/dashboard/homepage-youtube/': '/dashboard/site-content/',
        '/dashboard/appointments/': '/dashboard/messages/',
    }

    def test_dashboard_requires_login(self):
        for path in self.DASHBOARD_URLS:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/dashboard/login/', response['Location'])

    def test_dashboard_loads_when_authenticated(self):
        self.client.login(username='pastor_test', password='testpass123')
        for path in self.DASHBOARD_URLS:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(
                    response.status_code,
                    200,
                    msg=f'{path} returned {response.status_code}',
                )

    def test_dashboard_legacy_redirects(self):
        self.client.login(username='pastor_test', password='testpass123')
        for path, target in self.DASHBOARD_REDIRECTS.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertIn(response.status_code, (301, 302))
                self.assertIn(target, response['Location'])
