"""Load dummy audio resources for the /audio/ page (YouTube + thumbnails)."""

import urllib.request

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Resource

User = get_user_model()

AUDIO_SAMPLES = [
    {
        'title': 'Sunday Service — Kigali Fellowship',
        'description': 'Full audio message from our weekly gathering in Kigali.',
        'youtube_url': 'https://www.youtube.com/watch?v=RgKAFK5djSk',
        'is_featured': True,
    },
    {
        'title': 'Morning Devotional: Psalm 23',
        'description': 'Start your day meditating on the Good Shepherd.',
        'youtube_url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
        'is_featured': False,
    },
    {
        'title': 'Faith Over Fear — Night Prayer',
        'description': 'Finding peace in God when anxiety rises at night.',
        'youtube_url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
        'is_featured': True,
    },
    {
        'title': 'Worship & the Presence of God',
        'description': 'Teaching on authentic worship and encountering God.',
        'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'is_featured': False,
    },
    {
        'title': 'Healing Words for the Brokenhearted',
        'description': 'Comfort from Scripture for those walking through grief.',
        'youtube_url': 'https://www.youtube.com/watch?v=RgKAFK5djSk',
        'is_featured': False,
    },
    {
        'title': 'Family Altar: Leading Your Home in Prayer',
        'description': 'Practical steps to build a praying family.',
        'youtube_url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
        'is_featured': False,
    },
    {
        'title': 'The Power of Persistent Prayer',
        'description': 'Lessons from the parable of the persistent widow.',
        'youtube_url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
        'is_featured': False,
    },
    {
        'title': 'Grace That Transforms Lives',
        'description': 'How the Gospel changes us from the inside out.',
        'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'is_featured': False,
    },
]


class Command(BaseCommand):
    help = 'Populate /audio/ page with demo YouTube audio resources and cover images.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Delete existing audio resources before creating demo data.',
        )

    def handle(self, *args, **options):
        pastor = User.objects.filter(username='pastor_demo').first()
        if not pastor:
            call_command('populate_dummy')
            pastor = User.objects.filter(username='pastor_demo').first()

        if options['replace']:
            deleted, _ = Resource.objects.filter(
                resource_type=Resource.ResourceType.AUDIO
            ).delete()
            self.stdout.write(self.style.WARNING(f'Removed {deleted} existing audio rows.'))

        created = 0
        for i, data in enumerate(AUDIO_SAMPLES):
            resource, was_created = Resource.objects.get_or_create(
                title=data['title'],
                resource_type=Resource.ResourceType.AUDIO,
                defaults={
                    **data,
                    'is_published': True,
                    'published_at': timezone.now(),
                    'created_by': pastor,
                },
            )
            if not was_created:
                for key, value in data.items():
                    setattr(resource, key, value)
                resource.is_published = True
                resource.resource_type = Resource.ResourceType.AUDIO
                resource.save()

            if not resource.thumbnail:
                self._attach_thumbnail(resource, seed=300 + i)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f'Audio page ready: {created} messages with YouTube + thumbnails.')
        )

    def _attach_thumbnail(self, resource, seed=1):
        url = f'https://picsum.photos/seed/inziray-audio{seed}/640/360'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'InzirayAudioPopulate/1.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = response.read()
            resource.thumbnail.save(
                f'audio-{resource.slug}-thumb.jpg',
                ContentFile(data),
                save=True,
            )
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f'Thumbnail skip ({resource.title}): {exc}'))
