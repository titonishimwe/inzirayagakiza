"""Dashboard notification list filtering."""

from datetime import datetime

from django.db.models import Q
from .models import DashboardNotification


def get_available_years():
    dates = (
        DashboardNotification.objects.dates('created_at', 'year', order='DESC')
    )
    return [d.year for d in dates]


def filter_notifications(request_get):
    """
    Apply GET filters; returns (queryset, active_filters dict for template).
    """
    qs = DashboardNotification.objects.select_related(
        'related_contact',
        'related_question',
    ).order_by('-created_at')

    active = {}

    status = (request_get.get('status') or '').strip()
    if status == 'unread':
        qs = qs.filter(is_read=False)
        active['status'] = 'unread'
    elif status == 'read':
        qs = qs.filter(is_read=True)
        active['status'] = 'read'

    ntype = (request_get.get('type') or '').strip()
    if ntype:
        qs = qs.filter(notification_type=ntype)
        active['type'] = ntype

    year = (request_get.get('year') or '').strip()
    if year.isdigit():
        qs = qs.filter(created_at__year=int(year))
        active['year'] = year

    date_from = (request_get.get('date_from') or '').strip()
    if date_from:
        try:
            parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            qs = qs.filter(created_at__date__gte=parsed)
            active['date_from'] = date_from
        except ValueError:
            pass

    date_to = (request_get.get('date_to') or '').strip()
    if date_to:
        try:
            parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            qs = qs.filter(created_at__date__lte=parsed)
            active['date_to'] = date_to
        except ValueError:
            pass

    phone = (request_get.get('phone') or '').strip()
    if phone:
        qs = qs.filter(
            Q(message__icontains=phone)
            | Q(related_contact__whatsapp_phone__icontains=phone)
        )
        active['phone'] = phone

    email = (request_get.get('email') or '').strip()
    if email:
        qs = qs.filter(
            Q(message__icontains=email)
            | Q(related_contact__email__icontains=email)
            | Q(related_question__asker_email__icontains=email)
        )
        active['email'] = email

    q = (request_get.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(message__icontains=q)
            | Q(related_contact__full_name__icontains=q)
            | Q(related_question__asker_name__icontains=q)
            | Q(related_question__subject__icontains=q)
        )
        active['q'] = q

    return qs, active


def notification_type_choices():
    """Types present in DB plus standard choices."""
    db_types = (
        DashboardNotification.objects.values_list('notification_type', flat=True)
        .distinct()
    )
    labels = dict(DashboardNotification.NotificationType.choices)
    labels['appointment'] = 'Appointment (legacy)'
    seen = []
    for value in db_types:
        if value and value not in seen:
            seen.append((value, labels.get(value, value.replace('_', ' ').title())))
    for value, label in DashboardNotification.NotificationType.choices:
        if value not in [v for v, _ in seen]:
            seen.append((value, label))
    return seen
