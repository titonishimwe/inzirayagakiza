"""YouTube listing page — featured video pin and display helpers."""

from dataclasses import dataclass

from .models import ContentBlock, Resource
from .utils import youtube_thumbnail_urls, youtube_video_id, youtube_watch_url

DEFAULT_YOUTUBE_PAGE_FEATURED_URL = 'https://youtu.be/RXrvatSzY8I'

YOUTUBE_PAGE_BLOCKS = {
    'youtube_featured_video_url': (
        'YouTube page featured video URL',
        ContentBlock.BlockType.URL,
    ),
    'youtube_featured_video_title': (
        'YouTube page featured video title',
        ContentBlock.BlockType.TEXT,
    ),
    'youtube_featured_video_description': (
        'YouTube page featured video description',
        ContentBlock.BlockType.TEXT,
    ),
}


def ensure_youtube_page_blocks():
    for key, (label, block_type) in YOUTUBE_PAGE_BLOCKS.items():
        ContentBlock.objects.get_or_create(
            key=key,
            defaults={'label': label, 'block_type': block_type, 'value': ''},
        )


def _block_value(key, default=''):
    try:
        block = ContentBlock.objects.get(key=key, is_active=True)
        return block.value or default
    except ContentBlock.DoesNotExist:
        return default


@dataclass
class FeaturedVideoDisplay:
    """Featured row on /youtube/ (Resource or pinned URL)."""

    title: str
    description: str
    watch_url: str
    display_thumbnail_url: str
    display_thumbnail_fallback_url: str
    uses_youtube_cdn_thumbnail: bool = True
    pk: int | None = None

    @classmethod
    def from_resource(cls, resource: Resource) -> 'FeaturedVideoDisplay':
        return cls(
            title=resource.title,
            description=resource.description or '',
            watch_url=resource.watch_url,
            display_thumbnail_url=resource.display_thumbnail_url,
            display_thumbnail_fallback_url=resource.display_thumbnail_fallback_url,
            uses_youtube_cdn_thumbnail=resource.uses_youtube_cdn_thumbnail,
            pk=resource.pk,
        )

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        title: str = '',
        description: str = '',
    ) -> 'FeaturedVideoDisplay | None':
        video_id = youtube_video_id(url)
        if not video_id:
            return None
        thumbs = youtube_thumbnail_urls(video_id)
        return cls(
            title=title or 'Featured teaching',
            description=description,
            watch_url=youtube_watch_url(url),
            display_thumbnail_url=thumbs.get('maxres', ''),
            display_thumbnail_fallback_url=thumbs.get('hq', ''),
            uses_youtube_cdn_thumbnail=True,
            pk=None,
        )


def resolve_youtube_page_featured(resources: list) -> FeaturedVideoDisplay | None:
    """Pinned URL + title/description from site settings win over Resource labels."""
    ensure_youtube_page_blocks()
    pin_url = _block_value('youtube_featured_video_url', '').strip()
    pin_title = _block_value('youtube_featured_video_title', '').strip()
    pin_description = _block_value('youtube_featured_video_description', '').strip()

    if pin_url:
        pin_id = youtube_video_id(pin_url)
        if pin_id:
            for resource in resources:
                if youtube_video_id(resource.youtube_url) == pin_id:
                    # Keep Resource thumbnail / watch URL; use admin copy when set.
                    return FeaturedVideoDisplay(
                        title=pin_title or resource.title,
                        description=(
                            pin_description
                            if pin_description
                            else (resource.description or '')
                        ),
                        watch_url=resource.watch_url,
                        display_thumbnail_url=resource.display_thumbnail_url,
                        display_thumbnail_fallback_url=resource.display_thumbnail_fallback_url,
                        uses_youtube_cdn_thumbnail=resource.uses_youtube_cdn_thumbnail,
                        pk=resource.pk,
                    )
            return FeaturedVideoDisplay.from_url(
                pin_url,
                title=pin_title,
                description=pin_description,
            )

    featured = next((r for r in resources if r.is_featured), None)
    if featured:
        return FeaturedVideoDisplay.from_resource(featured)
    if resources:
        return FeaturedVideoDisplay.from_resource(resources[0])
    return None


def youtube_page_featured_form_initial():
    ensure_youtube_page_blocks()
    return {
        'youtube_page_video_url': _block_value(
            'youtube_featured_video_url',
            DEFAULT_YOUTUBE_PAGE_FEATURED_URL,
        ),
        'youtube_page_video_title': _block_value('youtube_featured_video_title', ''),
        'youtube_page_video_description': _block_value(
            'youtube_featured_video_description',
            'Why the cross is the center of the Christian message.',
        ),
    }


def save_youtube_page_featured(cleaned_data):
    ensure_youtube_page_blocks()

    def set_value(key, value):
        block = ContentBlock.objects.get(key=key)
        block.value = value or ''
        block.is_active = True
        block.save(update_fields=['value', 'is_active', 'updated_at'])

    set_value('youtube_featured_video_url', cleaned_data.get('youtube_page_video_url', ''))
    set_value('youtube_featured_video_title', cleaned_data.get('youtube_page_video_title', ''))
    set_value(
        'youtube_featured_video_description',
        cleaned_data.get('youtube_page_video_description', ''),
    )
