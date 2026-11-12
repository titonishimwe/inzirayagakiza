import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from core.models import Question


class Command(BaseCommand):
    help = 'Download placeholder thumbnails for answered questions with YouTube URL but no image.'

    def handle(self, *args, **options):
        qs = Question.objects.exclude(answer_youtube_url='').filter(
            answer_youtube_thumbnail=''
        )
        for q in qs:
            url = f'https://picsum.photos/seed/qa-answer-{q.pk}/640/360'
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'InzirayBackfill/1.0'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = response.read()
                q.answer_youtube_thumbnail.save(
                    f'qa-{q.pk}-thumb.jpg',
                    ContentFile(data),
                    save=True,
                )
                self.stdout.write(self.style.SUCCESS(f'Question {q.pk}: thumbnail saved'))
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'Question {q.pk}: {exc}'))
