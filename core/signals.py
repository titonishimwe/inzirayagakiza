from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import DashboardNotification, Question


# Contact messages appear in Dashboard → Messages (no duplicate notification row).


@receiver(post_save, sender=Question)
def notify_new_question(sender, instance, created, **kwargs):
    if not created:
        return
    DashboardNotification.objects.create(
        notification_type=DashboardNotification.NotificationType.QUESTION,
        title=f'New question from {instance.asker_name}',
        message=instance.question_text[:500],
        link=reverse('dashboard_answer_question', args=[instance.pk]),
        related_question=instance,
    )
