"""Point question notifications at the correct answer URL."""

from django.core.management.base import BaseCommand
from django.urls import reverse

from core.models import DashboardNotification


class Command(BaseCommand):
    help = 'Update dashboard notification links to use related question URLs.'

    def handle(self, *args, **options):
        updated = 0
        for notification in DashboardNotification.objects.filter(
            related_question__isnull=False,
        ).select_related('related_question'):
            notification.link = reverse(
                'dashboard_answer_question',
                args=[notification.related_question_id],
            )
            notification.save(update_fields=['link', 'updated_at'])
            updated += 1
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} notification link(s).'))
