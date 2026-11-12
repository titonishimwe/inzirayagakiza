"""Shared spiritual topics (QuestionCategory) for Q&A and media resources."""

from django.db.models import Count

from .models import QuestionCategory


# Logical topic definitions — one taxonomy for the whole site.
SITE_TOPICS = [
    {
        'name': 'Faith & Doubt',
        'slug': 'faith-doubt',
        'icon': 'bi-question-circle',
        'description': (
            'Belief, uncertainty, and trusting God. '
            'Use for Q&A on doubt; video/audio sermons on faith and assurance.'
        ),
    },
    {
        'name': 'Prayer & Worship',
        'slug': 'prayer-worship',
        'icon': 'bi-heart',
        'description': (
            'Prayer life, worship, and hearing from God. '
            'Use for worship teachings, prayer guides, and altar messages.'
        ),
    },
    {
        'name': 'Relationships & Family',
        'slug': 'relationships-family',
        'icon': 'bi-people',
        'description': (
            'Marriage, parenting, forgiveness, and home life. '
            'Use for family sermons and counsel-style teachings.'
        ),
    },
    {
        'name': 'Healing & Restoration',
        'slug': 'healing-restoration',
        'icon': 'bi-bandaid',
        'description': (
            'Grief, trauma, addiction recovery, and inner healing. '
            'Use for restoration testimonies and healing messages.'
        ),
    },
    {
        'name': 'Bible & Doctrine',
        'slug': 'bible-doctrine',
        'icon': 'bi-book',
        'description': (
            'Scripture, theology, and sound doctrine. '
            'Use for expository sermons, Bible studies, and teaching series.'
        ),
    },
    {
        'name': 'Anxiety & Life Stress',
        'slug': 'anxiety-life-stress',
        'icon': 'bi-cloud-rain',
        'description': (
            'Worry, depression, work pressure, and daily burdens. '
            'Use for encouragement and peace-focused messages.'
        ),
    },
    {
        'name': 'New Believers',
        'slug': 'new-believers',
        'icon': 'bi-sunrise',
        'description': (
            'First steps in Christ, baptism, church, and discipleship. '
            'Use for foundational gospel and “basics of faith” content.'
        ),
    },
    {
        'name': 'Sin & Repentance',
        'slug': 'sin-repentance',
        'icon': 'bi-arrow-repeat',
        'description': (
            'Guilt, temptation, confession, and freedom in Christ. '
            'Use for repentance, holiness, and grace-centered teaching.'
        ),
    },
]


def get_active_topics():
    return QuestionCategory.objects.filter(is_active=True).order_by(
        'sort_order', 'name'
    )


def get_topics_with_counts(qs):
    """Count published/filtered resources or questions per topic slug."""
    categories = get_active_topics()
    count_map = {
        row['category__slug']: row['count']
        for row in qs.filter(category__isnull=False)
        .values('category__slug')
        .annotate(count=Count('id'))
    }
    return [
        {'category': cat, 'count': count_map.get(cat.slug, 0)}
        for cat in categories
    ]


def topic_choices_for_form():
    return get_active_topics()


def published_resources_for_topic(category, resource_type=None, limit=6, exclude_pk=None):
    from .models import Resource

    qs = (
        Resource.objects.filter(
            is_published=True,
            category=category,
        )
        .select_related('category')
        .order_by('-is_featured', '-published_at')
    )
    if resource_type:
        qs = qs.filter(resource_type=resource_type)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return list(qs[:limit])


def get_topic_content_summary(category):
    """Counts and sample lists for a topic hub page."""
    from .qa_helpers import qa_public_queryset

    qa_qs = qa_public_queryset().filter(category=category)
    from .models import Resource

    video_qs = Resource.objects.filter(
        is_published=True,
        resource_type=Resource.ResourceType.VIDEO,
        category=category,
    ).exclude(youtube_url='')
    audio_qs = Resource.objects.filter(
        is_published=True,
        resource_type=Resource.ResourceType.AUDIO,
        category=category,
    ).exclude(youtube_url='')
    other_qs = Resource.objects.filter(
        is_published=True,
        category=category,
    ).exclude(
        resource_type__in=[
            Resource.ResourceType.VIDEO,
            Resource.ResourceType.AUDIO,
        ]
    )

    return {
        'qa_count': qa_qs.count(),
        'video_count': video_qs.count(),
        'audio_count': audio_qs.count(),
        'other_count': other_qs.count(),
        'qa_items': list(qa_qs.order_by('-is_featured', '-answered_at')[:8]),
        'videos': list(
            video_qs.order_by('-is_featured', '-published_at')[:6]
        ),
        'audio_items': list(
            audio_qs.order_by('-is_featured', '-published_at')[:6]
        ),
        'other_resources': list(
            other_qs.order_by('-is_featured', '-published_at')[:4]
        ),
    }


def get_unified_topics_with_counts():
    """Per-topic totals across Q&A, videos, and audio (for browse sidebars)."""
    from .models import Resource
    from .qa_helpers import qa_public_queryset

    categories = get_active_topics()
    qa_counts = {
        row['category__slug']: row['count']
        for row in qa_public_queryset()
        .filter(category__isnull=False)
        .values('category__slug')
        .annotate(count=Count('id'))
    }
    video_counts = {
        row['category__slug']: row['count']
        for row in Resource.objects.filter(
            is_published=True,
            resource_type=Resource.ResourceType.VIDEO,
            category__isnull=False,
        )
        .exclude(youtube_url='')
        .values('category__slug')
        .annotate(count=Count('id'))
    }
    audio_counts = {
        row['category__slug']: row['count']
        for row in Resource.objects.filter(
            is_published=True,
            resource_type=Resource.ResourceType.AUDIO,
            category__isnull=False,
        )
        .exclude(youtube_url='')
        .values('category__slug')
        .annotate(count=Count('id'))
    }
    result = []
    for cat in categories:
        qa_n = qa_counts.get(cat.slug, 0)
        vid_n = video_counts.get(cat.slug, 0)
        aud_n = audio_counts.get(cat.slug, 0)
        result.append({
            'category': cat,
            'qa_count': qa_n,
            'video_count': vid_n,
            'audio_count': aud_n,
            'total_count': qa_n + vid_n + aud_n,
        })
    return result


def get_related_for_question(question, limit=4):
    from .models import Resource
    from .qa_helpers import qa_public_queryset

    if not question.category_id:
        return {'qa': [], 'videos': [], 'audio': []}
    cat = question.category
    return {
        'qa': list(
            qa_public_queryset()
            .filter(category=cat)
            .exclude(pk=question.pk)
            .order_by('-answered_at')[:limit]
        ),
        'videos': published_resources_for_topic(
            cat, Resource.ResourceType.VIDEO, limit=limit
        ),
        'audio': published_resources_for_topic(
            cat, Resource.ResourceType.AUDIO, limit=limit
        ),
    }
