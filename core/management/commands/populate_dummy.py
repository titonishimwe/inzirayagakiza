import urllib.request
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from django.core.management import call_command

from core.models import (
    ContactMessage,
    ContentBlock,
    Question,
    QuestionCategory,
    Resource,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate the database with sample content for development and demos.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing demo content before populating (keeps users).',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_demo_data()
            self.stdout.write(self.style.WARNING('Cleared demo content.'))

        self._content_blocks()
        call_command('populate_categories')
        pastor = self._ensure_pastor_user()
        self._resources(pastor)
        self._questions(pastor)
        self._contact_messages()
        self.stdout.write(self.style.SUCCESS('Dummy content populated successfully.'))

    def _clear_demo_data(self):
        Resource.objects.all().delete()
        Question.objects.all().delete()
        ContactMessage.objects.all().delete()

    def _content_blocks(self):
        blocks = {
            'hero_tagline': 'Teaching Gospel to the Nation',
            'hero_title': "Inzira y'ubugingo",
            'hero_subtitle': (
                'Equipping believers, spreading truth, and transforming lives '
                'through the Word of God.'
            ),
            'home_youtube_video_url': 'https://youtu.be/qJjcI2wfuqo',
            'home_youtube_video_title': '',
            'home_youtube_section_title': 'Latest from YouTube',
            'home_youtube_section_text': (
                'Watch our recent teachings and subscribe to stay updated with the Gospel message. '
                'We regularly upload full services and Bible studies.'
            ),
            'home_youtube_channel_url': 'https://www.youtube.com/@INZIRAYUBUGINGOTV/videos',
        }
        from core.home_youtube import ensure_home_youtube_blocks
        ensure_home_youtube_blocks()
        for key, value in blocks.items():
            if key.startswith('home_youtube_') or key == 'featured_youtube':
                block_type = ContentBlock.BlockType.URL if 'url' in key else ContentBlock.BlockType.TEXT
            elif key.startswith('stat_'):
                block_type = ContentBlock.BlockType.NUMBER
            else:
                block_type = ContentBlock.BlockType.TEXT
            ContentBlock.objects.update_or_create(
                key=key,
                defaults={
                    'label': key.replace('_', ' ').title(),
                    'value': value,
                    'block_type': block_type,
                    'is_active': True,
                },
            )

    def _ensure_pastor_user(self):
        user, created = User.objects.get_or_create(
            username='pastor_demo',
            defaults={
                'email': 'pastor@inziray.demo',
                'first_name': 'Jean',
                'last_name': 'Pastor',
                'is_staff': False,
            },
        )
        if created:
            user.set_password('demo1234')
            user.save()
            self.stdout.write('Created demo pastor user: pastor_demo / demo1234')
        pastor_group, _ = Group.objects.get_or_create(name='Pastor')
        user.groups.add(pastor_group)
        return user

    def _resources(self, pastor):
        samples = [
            {
                'title': 'The Path of Salvation — Part 1',
                'description': 'An introduction to grace, faith, and repentance in Christ.',
                'resource_type': Resource.ResourceType.VIDEO,
                'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'is_featured': True,
            },
            {
                'title': 'Walking in the Spirit',
                'description': 'Teaching on living by the Spirit rather than the flesh.',
                'resource_type': Resource.ResourceType.VIDEO,
                'youtube_url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
                'is_featured': False,
            },
            {
                'title': 'Sunday Service — Kigali Fellowship',
                'description': 'Full audio recording from the weekly gathering.',
                'resource_type': Resource.ResourceType.AUDIO,
                'youtube_url': 'https://www.youtube.com/watch?v=RgKAFK5djSk',
                'is_featured': True,
            },
            {
                'title': 'Morning Devotional: Psalm 23',
                'description': 'Short audio devotional for daily meditation.',
                'resource_type': Resource.ResourceType.AUDIO,
                'youtube_url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
                'is_featured': False,
            },
            {
                'title': 'Faith Over Fear — Night Prayer',
                'description': 'Finding peace in God when anxiety rises at night.',
                'resource_type': Resource.ResourceType.AUDIO,
                'youtube_url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
                'is_featured': True,
            },
            {
                'title': 'Worship & the Presence of God',
                'description': 'Teaching on authentic worship and encountering God.',
                'resource_type': Resource.ResourceType.AUDIO,
                'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'is_featured': False,
            },
            {
                'title': 'Healing Words for the Brokenhearted',
                'description': 'Comfort from Scripture for those walking through grief.',
                'resource_type': Resource.ResourceType.AUDIO,
                'youtube_url': 'https://www.youtube.com/watch?v=RgKAFK5djSk',
                'is_featured': False,
            },
            {
                'title': 'Family Altar: Leading Your Home in Prayer',
                'description': 'Practical steps to build a praying family.',
                'resource_type': Resource.ResourceType.AUDIO,
                'youtube_url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
                'is_featured': False,
            },
            {
                'title': 'The Power of Persistent Prayer',
                'description': 'Never give up — lessons from the parable of the persistent widow.',
                'resource_type': Resource.ResourceType.AUDIO,
                'youtube_url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
                'is_featured': False,
            },
            {
                'title': 'Romans Study Guide — Chapters 1–4',
                'description': 'PDF notes for small group Bible study.',
                'resource_type': Resource.ResourceType.PDF,
                'external_url': 'https://www.w3.org/WAI/WCAG21/Techniques/pdf/img/table-word.pdf',
                'is_featured': False,
            },
            {
                'title': 'Foundations of Faith — Student Handbook',
                'description': 'Comprehensive PDF for new believers class.',
                'resource_type': Resource.ResourceType.PDF,
                'external_url': 'https://www.africau.edu/images/default/sample.pdf',
                'is_featured': True,
            },
            {
                'title': 'The Great Commission — Slide Deck',
                'description': 'Presentation slides for evangelism training.',
                'resource_type': Resource.ResourceType.SLIDE,
                'external_url': 'https://example.com/slides/great-commission',
                'is_featured': False,
            },
            {
                'title': 'Fruit of the Spirit — Teaching Slides',
                'description': 'Visual slides covering Galatians 5:22–23.',
                'resource_type': Resource.ResourceType.SLIDE,
                'external_url': 'https://example.com/slides/fruit-of-spirit',
                'is_featured': False,
            },
            {
                'title': 'Easter Sunday Sermon 2025',
                'description': 'Resurrection message: He is risen indeed.',
                'resource_type': Resource.ResourceType.SERMON,
                'youtube_url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
                'is_featured': True,
            },
            {
                'title': 'Prayer and Fasting — Complete Message',
                'description': 'Sermon on drawing near to God through prayer and fasting.',
                'resource_type': Resource.ResourceType.SERMON,
                'youtube_url': 'https://www.youtube.com/watch?v=RgKAFK5djSk',
                'is_featured': False,
            },
        ]
        for i, data in enumerate(samples):
            resource, _ = Resource.objects.get_or_create(
                title=data['title'],
                defaults={
                    **data,
                    'is_published': True,
                    'published_at': timezone.now() - timedelta(days=i * 3),
                    'created_by': pastor,
                },
            )
            if (
                resource.resource_type in (
                    Resource.ResourceType.VIDEO,
                    Resource.ResourceType.AUDIO,
                )
                and resource.youtube_url
                and not resource.thumbnail
            ):
                self._attach_sample_thumbnail(resource, seed=i + 1)

    def _attach_sample_thumbnail(self, resource, seed=1):
        """Download a placeholder image into the uploaded thumbnail field."""
        url = f'https://picsum.photos/seed/inziray{seed}/640/360'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'InzirayPopulate/1.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = response.read()
            filename = f'{resource.slug}-thumb.jpg'
            resource.thumbnail.save(filename, ContentFile(data), save=True)
        except Exception as exc:
            self.stdout.write(
                self.style.WARNING(f'Could not fetch thumbnail for {resource.title}: {exc}')
            )

    def _cat(self, slug):
        return QuestionCategory.objects.filter(slug=slug).first()

    def _questions(self, pastor):
        Question.objects.update_or_create(
            asker_email='marie@example.com',
            defaults={
                'asker_name': 'Marie Uwimana',
                'category': self._cat('new-believers'),
                'subject': 'Baptism timing',
                'question_text': (
                    'I accepted Christ last month. When is the right time to be baptized?'
                ),
                'status': Question.Status.PENDING,
            },
        )

        paul, _ = Question.objects.update_or_create(
            asker_email='paul@example.com',
            defaults={
                'asker_name': 'Paul Nkurunziza',
                'category': self._cat('relationships-family'),
                'subject': 'Forgiveness and reconciliation',
                'question_text': (
                    'How do I forgive someone who is not asking for forgiveness?'
                ),
                'status': Question.Status.ANSWERED,
                'answer_text': (
                    'Forgiveness is a command and a choice before it is a feeling. '
                    'You release the debt to God and pray for the person. Reconciliation '
                    'requires repentance on both sides, but forgiveness can happen unilaterally.'
                ),
                'answer_youtube_url': '',
                'is_public': True,
                'answered_by': pastor,
                'answered_at': timezone.now() - timedelta(days=2),
            },
        )
        paul_resources = Resource.objects.filter(is_published=True)[:2]
        if paul_resources:
            paul.recommended_resources.set(paul_resources)

        grace, _ = Question.objects.update_or_create(
            asker_email='grace@example.com',
            defaults={
                'asker_name': 'Grace Mukamana',
                'category': self._cat('sin-repentance'),
                'subject': 'Music and holiness',
                'question_text': 'Can Christians listen to secular music?',
                'status': Question.Status.ANSWERED,
                'answer_text': '',
                'answer_youtube_url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
                'is_public': True,
                'answered_by': pastor,
                'answered_at': timezone.now() - timedelta(days=7),
            },
        )
        grace.recommended_resources.clear()
        if grace.answer_youtube_url and not grace.answer_youtube_thumbnail:
            self._attach_answer_thumbnail(grace, seed=201)

        emmanuel, _ = Question.objects.update_or_create(
            asker_email='emmanuel.qa@example.com',
            defaults={
                'asker_name': 'Emmanuel Bizimana',
                'category': self._cat('bible-doctrine'),
                'subject': 'How do I start reading the Bible?',
                'question_text': 'I am a new believer. Where should I begin?',
                'status': Question.Status.ANSWERED,
                'answer_text': (
                    'Start with the Gospel of John, then Romans. Read a short passage daily, '
                    'pray before you read, and write one verse that speaks to you.'
                ),
                'answer_youtube_url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
                'is_public': True,
                'answered_by': pastor,
                'answered_at': timezone.now() - timedelta(days=1),
            },
        )
        video_resources = Resource.objects.filter(
            resource_type=Resource.ResourceType.VIDEO,
            is_published=True,
        )[:1]
        if video_resources:
            emmanuel.recommended_resources.set(video_resources)
        if emmanuel.answer_youtube_url and not emmanuel.answer_youtube_thumbnail:
            self._attach_answer_thumbnail(emmanuel, seed=202)

        Question.objects.update_or_create(
            asker_email='alice.faith@example.com',
            defaults={
                'asker_name': 'Alice Uwase',
                'category': self._cat('faith-doubt'),
                'subject': 'God feels distant',
                'question_text': (
                    'I pray but feel nothing. Does that mean God has left me?'
                ),
                'status': Question.Status.ANSWERED,
                'answer_text': (
                    'Feelings fluctuate; faith rests on God\'s promises, not emotions. '
                    'Keep seeking Him in Scripture and community — He is nearer than you feel.'
                ),
                'answer_youtube_url': '',
                'is_public': True,
                'answered_by': pastor,
                'answered_at': timezone.now() - timedelta(days=4),
            },
        )
        jean, _ = Question.objects.update_or_create(
            asker_email='jean.anxiety@example.com',
            defaults={
                'asker_name': 'Jean Claude',
                'category': self._cat('anxiety-life-stress'),
                'subject': 'Overwhelming worry',
                'question_text': 'I cannot stop worrying about my family and future.',
                'status': Question.Status.ANSWERED,
                'answer_text': (
                    'Cast your cares on Him, for He cares for you (1 Peter 5:7). '
                    'Practical steps: limit news intake, pray with specifics, and speak with a trusted believer.'
                ),
                'answer_youtube_url': 'https://www.youtube.com/watch?v=RgKAFK5djSk',
                'is_public': True,
                'answered_by': pastor,
                'answered_at': timezone.now() - timedelta(days=3),
            },
        )
        if jean.answer_youtube_url and not jean.answer_youtube_thumbnail:
            self._attach_answer_thumbnail(jean, seed=203)

    def _attach_answer_thumbnail(self, question, seed=1):
        url = f'https://picsum.photos/seed/qa-answer{seed}/640/360'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'InzirayPopulate/1.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = response.read()
            filename = f'qa-answer-{question.pk or seed}-thumb.jpg'
            question.answer_youtube_thumbnail.save(filename, ContentFile(data), save=True)
        except Exception as exc:
            self.stdout.write(
                self.style.WARNING(
                    f'Could not fetch answer thumbnail for question {question.pk}: {exc}'
                )
            )

    def _contact_messages(self):
        samples = [
            {
                'full_name': 'David Habimana',
                'email': 'david@example.com',
                'whatsapp_phone': '0788123456',
                'message': 'I would like counseling about marriage preparation.',
                'status': ContactMessage.Status.PENDING,
            },
            {
                'full_name': 'Sarah Ingabire',
                'email': '',
                'whatsapp_phone': '0788987654',
                'message': 'Requesting prayer and guidance for a new ministry role.',
                'status': ContactMessage.Status.READ,
            },
            {
                'full_name': 'Emmanuel Bizimana',
                'email': 'emmanuel@example.com',
                'whatsapp_phone': '0788555123',
                'message': 'Follow-up after Sunday service — thank you.',
                'status': ContactMessage.Status.REPLIED,
            },
        ]
        for data in samples:
            ContactMessage.objects.get_or_create(
                full_name=data['full_name'],
                whatsapp_phone=data['whatsapp_phone'],
                defaults=data,
            )
