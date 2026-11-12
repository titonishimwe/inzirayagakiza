"""Helpers for public Q&A pages and dashboard previews."""

from django.db.models import Count, Q

from .models import Question


def qa_public_queryset():
    return (
        Question.objects.filter(
            status=Question.Status.ANSWERED,
            is_public=True,
        )
        .annotate(resource_count=Count('recommended_resources'))
        .filter(
            Q(answer_text__gt='')
            | Q(answer_youtube_url__gt='')
            | Q(resource_count__gt=0)
        )
        .distinct()
        .select_related('category', 'answered_by')
        .prefetch_related('recommended_resources')
    )


def question_display_title(question):
    if question.subject:
        return question.subject
    text = (question.question_text or '').strip()
    if len(text) > 120:
        return text[:117] + '…'
    return text or 'Question'


def get_featured_questions(limit=20):
    base = qa_public_queryset()
    featured = list(base.filter(is_featured=True).order_by('-answered_at', '-created_at')[:limit])
    if len(featured) >= limit:
        return featured
    ids = [q.pk for q in featured]
    remaining = limit - len(featured)
    extra = base.exclude(pk__in=ids).order_by('-answered_at', '-created_at')[:remaining]
    return featured + list(extra)


def get_sidebar_questions(limit=20, exclude_pks=None):
    qs = qa_public_queryset().order_by('-is_featured', '-answered_at', '-created_at')
    if exclude_pks:
        qs = qs.exclude(pk__in=exclude_pks)
    return list(qs[:limit])


def get_categories_with_counts():
    from .models import QuestionCategory

    categories = QuestionCategory.objects.filter(is_active=True)
    count_map = {
        row['category__slug']: row['count']
        for row in qa_public_queryset()
        .filter(category__isnull=False)
        .values('category__slug')
        .annotate(count=Count('id'))
    }
    return [
        {'category': cat, 'count': count_map.get(cat.slug, 0)}
        for cat in categories
    ]
