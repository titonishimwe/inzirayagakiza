from django.core.management.base import BaseCommand

from core.category_helpers import SITE_TOPICS
from core.models import QuestionCategory


class Command(BaseCommand):
    help = 'Create or update site-wide spiritual topics (Q&A, video, audio, etc.).'

    def handle(self, *args, **options):
        for order, topic in enumerate(SITE_TOPICS):
            QuestionCategory.objects.update_or_create(
                slug=topic['slug'],
                defaults={
                    'name': topic['name'],
                    'icon': topic['icon'],
                    'description': topic['description'],
                    'sort_order': order,
                    'is_active': True,
                },
            )
        self.stdout.write(
            self.style.SUCCESS(f'Synced {len(SITE_TOPICS)} site topics.')
        )
