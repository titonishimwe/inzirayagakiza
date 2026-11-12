"""Populate /youtube/ with demo video resources (YouTube URL + uploaded thumbnails)."""

import urllib.request

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Resource

User = get_user_model()

YOUTUBE_SAMPLES = [
    {
        'title': 'The Path of Salvation — Part 1',
        'description': 'An introduction to grace, faith, and repentance in Christ.',
        'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'is_featured': True,
    },
    {
        'title': 'Walking in the Spirit',
        'description': 'Teaching on living by the Spirit rather than the flesh.',
        'youtube_url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
        'is_featured': False,
    },
    {
        'title': 'Faith That Moves Mountains',
        'description': 'Understanding biblical faith and trusting God in trials.',
        'youtube_url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
        'is_featured': False,
    },
    {
        'title': 'The Power of the Cross',
        'description': 'Why the cross is the center of the Christian message.',
        'youtube_url': 'https://youtu.be/RXrvatSzY8I',
        'is_featured': True,
    },
    {
        'title': 'Living as Salt and Light',
        'description': 'How believers influence the world for Christ.',
        'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'is_featured': False,
    },
    {
        'title': 'Hope in Difficult Seasons',
        'description': 'Encouragement for those walking through hardship.',
        'youtube_url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
        'is_featured': False,
    },
    {
        'title': 'The Lord\'s Prayer Explained',
        'description': 'Line-by-line teaching on how Jesus taught us to pray.',
        'youtube_url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
        'is_featured': False,
    },
    {
        'title': 'Easter: He Is Risen',
        'description': 'Celebrating the resurrection and what it means for us.',
        'youtube_url': 'https://www.youtube.com/watch?v=RgKAFK5djSk',
        'is_featured': False,
    },
    {
        'title': 'Discipleship: Following Jesus Daily',
        'description': 'Practical steps to grow as a disciple every day.',
        'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'is_featured': False,
    },
]


class Command(BaseCommand):
    help = 'Populate the YouTube page with demo videos (thumbnail images + YouTube links).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Delete existing video resources before creating demo data.',
        )

    def handle(self, *args, **options):
        pastor = User.objects.filter(username='pastor_demo').first()
        if not pastor:
            call_command('populate_dummy')
            pastor = User.objects.filter(username='pastor_demo').first()

        if options['replace']:
            deleted, _ = Resource.objects.filter(
                resource_type=Resource.ResourceType.VIDEO
            ).delete()
            self.stdout.write(self.style.WARNING(f'Removed {deleted} existing video rows.'))

        for i, data in enumerate(YOUTUBE_SAMPLES):
            resource, was_created = Resource.objects.get_or_create(
                title=data['title'],
                resource_type=Resource.ResourceType.VIDEO,
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
                resource.resource_type = Resource.ResourceType.VIDEO
                resource.save()

            if not resource.thumbnail:
                self._attach_thumbnail(resource, seed=100 + i)

        count = Resource.objects.filter(
            resource_type=Resource.ResourceType.VIDEO,
            is_published=True,
        ).exclude(youtube_url='').exclude(thumbnail='').count()
        self.stdout.write(
            self.style.SUCCESS(f'YouTube page ready: {count} videos with thumbnails.')
        )

    def _attach_thumbnail(self, resource, seed=1):
        url = f'https://picsum.photos/seed/inziray-yt{seed}/640/360'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'InzirayYouTubePopulate/1.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = response.read()
            resource.thumbnail.save(
                f'yt-{resource.slug}-thumb.jpg',
                ContentFile(data),
                save=True,
            )
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f'Thumbnail skip ({resource.title}): {exc}'))
