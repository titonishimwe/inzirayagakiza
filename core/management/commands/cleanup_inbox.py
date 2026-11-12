"""Remove legacy contact notifications (inbox is ContactMessage-only)."""

from django.core.management.base import BaseCommand

from core.models import DashboardNotification


class Command(BaseCommand):
    help = (
        'Delete legacy Get in Touch dashboard notifications. '
        'Messages live in ContactMessage only.'
    )

    def handle(self, *args, **options):
        deleted, _ = DashboardNotification.objects.filter(
            notification_type=DashboardNotification.NotificationType.CONTACT,
        ).delete()
        self.stdout.write(
            self.style.SUCCESS(f'Removed {deleted} legacy contact notification(s).')
        )
