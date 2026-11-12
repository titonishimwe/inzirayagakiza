"""Filters and pagination helpers for public listing pages."""

from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Q

from .models import QuestionCategory, Resource

PUBLIC_GRID_PAGE_SIZE = 12
QA_PAGE_SIZE = 10
SEARCH_PAGE_SIZE = 20
DASHBOARD_RESOURCE_PAGE_SIZE = 25


def get_resource_years(qs=None):
    base = qs if qs is not None else Resource.objects.filter(is_published=True)
    dates = base.dates('published_at', 'year', order='DESC')
    return [d.year for d in dates]


def filter_published_resources(qs, request_get, *, require_youtube=False):
    """Apply common GET filters; returns (queryset, active_filters dict)."""
    active = {}

    if require_youtube:
        qs = qs.exclude(youtube_url='')

    q = (request_get.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )
        active['q'] = q

    year = (request_get.get('year') or '').strip()
    if year.isdigit():
        year_int = int(year)
        qs = qs.filter(published_at__year=year_int)
        active['year'] = year_int

    featured = (request_get.get('featured') or '').strip()
    if featured == '1':
        qs = qs.filter(is_featured=True)
        active['featured'] = '1'

    category_slug = (request_get.get('category') or '').strip()
    if category_slug:
        cat = QuestionCategory.objects.filter(
            slug=category_slug, is_active=True
        ).first()
        if cat:
            qs = qs.filter(category=cat)
            active['category'] = category_slug

    sort = (request_get.get('sort') or 'newest').strip()
    if sort not in ('newest', 'oldest', 'title'):
        sort = 'newest'
    if sort == 'oldest':
        qs = qs.order_by('published_at', 'title')
        active['sort'] = 'oldest'
    elif sort == 'title':
        qs = qs.order_by('title')
        active['sort'] = 'title'
    else:
        qs = qs.order_by('-is_featured', '-published_at', 'title')

    return qs, active


def _pagination_context(page_obj, request_get):
    query_params = request_get.copy()
    query_params.pop('page', None)
    return {
        'page_obj': page_obj,
        'items': page_obj.object_list,
        'filtered_count': page_obj.paginator.count,
        'filter_querystring': query_params.urlencode(),
    }


def paginate_queryset(qs, request_get, per_page):
    """Return page_obj and pagination context for templates."""
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(request_get.get('page', 1))
    return _pagination_context(page_obj, request_get)


def paginate_list(items, request_get, per_page):
    """Paginate a materialized list (e.g. YouTube grid after featured exclusion)."""
    paginator = Paginator(items, per_page)
    page_obj = paginator.get_page(request_get.get('page', 1))
    return _pagination_context(page_obj, request_get)


def listing_filter_context(request_get, qs, *, per_page, require_youtube=False):
    """Filter then paginate a resource queryset."""
    from .category_helpers import get_topics_with_counts

    count_qs = qs
    if require_youtube:
        count_qs = count_qs.exclude(youtube_url='')
    topics_with_counts = get_topics_with_counts(count_qs)

    qs, active_filters = filter_published_resources(
        qs, request_get, require_youtube=require_youtube
    )
    active_category = None
    if active_filters.get('category'):
        active_category = QuestionCategory.objects.filter(
            slug=active_filters['category'], is_active=True
        ).first()

    pagination = paginate_queryset(qs, request_get, per_page)
    return {
        **pagination,
        'active_filters': active_filters,
        'has_filters': bool(active_filters),
        'years': get_resource_years(count_qs),
        'topics_with_counts': topics_with_counts,
        'active_category': active_category,
    }


def filter_search_resources(qs, request_get):
    active = {}
    q = (request_get.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        active['q'] = q

    rtype = (request_get.get('type') or '').strip()
    type_map = {
        'video': Resource.ResourceType.VIDEO,
        'audio': Resource.ResourceType.AUDIO,
        'pdf': Resource.ResourceType.PDF,
        'slides': Resource.ResourceType.SLIDE,
        'sermon': Resource.ResourceType.SERMON,
    }
    if rtype in type_map:
        qs = qs.filter(resource_type=type_map[rtype])
        active['type'] = rtype

    qs = qs.order_by('-published_at', 'title')
    return qs, active
