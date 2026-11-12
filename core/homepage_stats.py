"""Homepage hero statistics — counted from published resources."""

from .models import Resource


def format_stat_count(count: int) -> str:
    """Display count on the homepage hero (e.g. 48, 1.2k+)."""
    if count >= 1000:
        value = count / 1000
        text = f'{value:.1f}'.rstrip('0').rstrip('.')
        return f'{text}k+'
    if count > 0:
        return f'{count}+'
    return '0'


def get_homepage_resource_stats():
    """Return formatted stat labels and raw counts for the public site and dashboard."""
    published = Resource.objects.filter(is_published=True)
    sermon_count = published.filter(
        resource_type__in=[
            Resource.ResourceType.VIDEO,
            Resource.ResourceType.SERMON,
        ],
    ).count()
    audio_count = published.filter(
        resource_type=Resource.ResourceType.AUDIO,
    ).count()
    pdf_count = published.filter(
        resource_type__in=[
            Resource.ResourceType.PDF,
            Resource.ResourceType.SLIDE,
        ],
    ).count()
    return {
        'stat_sermons': format_stat_count(sermon_count),
        'stat_audio': format_stat_count(audio_count),
        'stat_pdfs': format_stat_count(pdf_count),
        'counts': {
            'sermons': sermon_count,
            'audio': audio_count,
            'pdfs': pdf_count,
        },
    }
