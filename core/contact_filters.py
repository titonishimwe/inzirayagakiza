"""Dashboard inbox filters for Get in Touch messages."""

from datetime import datetime

from django.db.models import Count, Q

from .models import ContactMessage


def get_contact_years():
    dates = ContactMessage.objects.dates('created_at', 'year', order='DESC')
    return [d.year for d in dates]


def get_contact_status_counts():
    """Live counts per status for dashboard stats and filter tabs."""
    counts = {choice[0]: 0 for choice in ContactMessage.Status.choices}
    for row in ContactMessage.objects.values('status').annotate(c=Count('id')):
        counts[row['status']] = row['c']
    counts['all'] = sum(counts.values())
    return counts


def filter_contact_messages(request_get):
    qs = ContactMessage.objects.all().order_by('-created_at')
    active = {}

    status = (request_get.get('status') or '').strip()
    if status in dict(ContactMessage.Status.choices):
        qs = qs.filter(status=status)
        active['status'] = status

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
            Q(whatsapp_phone__icontains=phone) | Q(message__icontains=phone)
        )
        active['phone'] = phone

    email = (request_get.get('email') or '').strip()
    if email:
        qs = qs.filter(Q(email__icontains=email) | Q(message__icontains=email))
        active['email'] = email

    q = (request_get.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(full_name__icontains=q)
            | Q(message__icontains=q)
            | Q(email__icontains=q)
            | Q(whatsapp_phone__icontains=q)
            | Q(admin_notes__icontains=q)
        )
        active['q'] = q

    return qs, active
