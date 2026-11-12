"""Dashboard Q&A inbox filters."""

from datetime import datetime

from django.db.models import Count, Q

from .models import Question, QuestionCategory


def get_question_years():
    dates = Question.objects.dates('created_at', 'year', order='DESC')
    return [d.year for d in dates]


def get_question_status_counts():
    counts = {choice[0]: 0 for choice in Question.Status.choices}
    for row in Question.objects.values('status').annotate(c=Count('id')):
        counts[row['status']] = row['c']
    counts['all'] = sum(counts.values())
    return counts


def get_question_category_choices():
    return QuestionCategory.objects.filter(is_active=True).order_by('sort_order', 'name')


def filter_questions(request_get):
    qs = (
        Question.objects.select_related('category', 'answered_by')
        .prefetch_related('recommended_resources')
        .order_by('-created_at')
    )
    active = {}

    status = (request_get.get('status') or '').strip()
    if status in dict(Question.Status.choices):
        qs = qs.filter(status=status)
        active['status'] = status

    category = (request_get.get('category') or '').strip()
    if category:
        cat = QuestionCategory.objects.filter(slug=category, is_active=True).first()
        if cat:
            qs = qs.filter(category=cat)
            active['category'] = category

    visibility = (request_get.get('visibility') or '').strip()
    if visibility == 'public':
        qs = qs.filter(is_public=True, status=Question.Status.ANSWERED)
        active['visibility'] = visibility
    elif visibility == 'private':
        qs = qs.filter(is_public=False)
        active['visibility'] = visibility
    elif visibility == 'featured':
        qs = qs.filter(
            is_public=True,
            is_featured=True,
            status=Question.Status.ANSWERED,
        )
        active['visibility'] = visibility

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

    email = (request_get.get('email') or '').strip()
    if email:
        qs = qs.filter(Q(asker_email__icontains=email) | Q(asker_name__icontains=email))
        active['email'] = email

    q = (request_get.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(asker_name__icontains=q)
            | Q(asker_email__icontains=q)
            | Q(subject__icontains=q)
            | Q(question_text__icontains=q)
            | Q(answer_text__icontains=q)
            | Q(category__name__icontains=q)
        )
        active['q'] = q

    return qs, active
