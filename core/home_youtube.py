"""Homepage featured YouTube section (ContentBlock-backed)."""

from .models import ContentBlock, Resource
from .utils import youtube_thumbnail_urls, youtube_video_id, youtube_watch_url

DEFAULT_FEATURED_VIDEO_URL = 'https://youtu.be/qJjcI2wfuqo'

DEFAULT_SECTION_TITLE = 'Latest from YouTube'
DEFAULT_SECTION_TEXT = (
    'Watch our recent teachings and subscribe to stay updated with the Gospel message. '
    'We regularly upload full services and Bible studies.'
)
DEFAULT_CHANNEL_URL = 'https://www.youtube.com/@INZIRAYUBUGINGOTV/videos'

HOME_YOUTUBE_BLOCKS = {
    'home_youtube_video_url': (
        'Homepage featured YouTube URL',
        ContentBlock.BlockType.URL,
    ),
    'home_youtube_video_title': (
        'Homepage featured video title',
        ContentBlock.BlockType.TEXT,
    ),
    'home_youtube_thumbnail': (
        'Homepage featured video thumbnail',
        ContentBlock.BlockType.IMAGE,
    ),
    'home_youtube_section_title': (
        'Homepage YouTube section heading',
        ContentBlock.BlockType.TEXT,
    ),
    'home_youtube_section_text': (
        'Homepage YouTube section description',
        ContentBlock.BlockType.TEXT,
    ),
    'home_youtube_channel_url': (
        'Homepage YouTube channel link',
        ContentBlock.BlockType.URL,
    ),
}


def ensure_home_youtube_blocks():
    for key, (label, block_type) in HOME_YOUTUBE_BLOCKS.items():
        ContentBlock.objects.get_or_create(
            key=key,
            defaults={
                'label': label,
                'block_type': block_type,
                'value': '',
            },
        )


def _get_block(key):
    try:
        return ContentBlock.objects.get(key=key, is_active=True)
    except ContentBlock.DoesNotExist:
        return None


def _block_value(key, default=''):
    block = _get_block(key)
    if not block:
        return default
    if block.block_type == ContentBlock.BlockType.IMAGE:
        return ''
    return block.value or default


def _featured_youtube_resource():
    return (
        Resource.objects.filter(
            is_published=True,
            resource_type=Resource.ResourceType.VIDEO,
        )
        .exclude(youtube_url='')
        .order_by('-is_featured', '-published_at')
        .first()
    )


def build_home_youtube_feature():
    """Context dict for the homepage YouTube teaser section."""
    video_url = _block_value('home_youtube_video_url', '').strip()
    if not video_url:
        video_url = _block_value('featured_youtube', '').strip()
    linked_resource = None
    if not video_url:
        linked_resource = _featured_youtube_resource()
        if linked_resource:
            video_url = linked_resource.youtube_url.strip()

    video_id = youtube_video_id(video_url)
    watch_url = youtube_watch_url(video_url) if video_id else video_url

    thumb_block = _get_block('home_youtube_thumbnail')
    thumbnail_url = ''
    thumbnail_fallback_url = ''
    thumbnail_is_custom = False
    if thumb_block and thumb_block.image:
        thumbnail_url = thumb_block.image.url
        thumbnail_is_custom = True
    elif video_id:
        thumbs = youtube_thumbnail_urls(video_id)
        thumbnail_url = thumbs.get('maxres', '')
        thumbnail_fallback_url = thumbs.get('hq', '')
    elif linked_resource and linked_resource.thumbnail:
        thumbnail_url = linked_resource.thumbnail.url
        thumbnail_is_custom = True

    section_title = _block_value('home_youtube_section_title', DEFAULT_SECTION_TITLE)
    section_text = _block_value('home_youtube_section_text', DEFAULT_SECTION_TEXT)
    channel_url = (
        _block_value('home_youtube_channel_url', '').strip()
        or _block_value('youtube_channel_url', '').strip()
        or DEFAULT_CHANNEL_URL
    )
    video_title = _block_value('home_youtube_video_title', '').strip()
    if not video_title and linked_resource:
        video_title = linked_resource.title
    video_description = ''
    if linked_resource and youtube_video_id(linked_resource.youtube_url) == video_id:
        video_description = linked_resource.description or ''

    return {
        'watch_url': watch_url,
        'thumbnail_url': thumbnail_url,
        'thumbnail_fallback_url': thumbnail_fallback_url,
        'thumbnail_is_custom': thumbnail_is_custom,
        'video_title': video_title,
        'video_description': video_description,
        'section_title': section_title,
        'section_text': section_text,
        'channel_url': channel_url,
        'is_configured': bool(thumbnail_url or video_id),
        'video_id': video_id,
        'uses_youtube_cdn': bool(video_id) and not thumbnail_is_custom,
    }


def home_youtube_form_initial():
    feat = build_home_youtube_feature()
    thumb_block = _get_block('home_youtube_thumbnail')
    return {
        'video_url': _block_value('home_youtube_video_url', '') or _block_value('featured_youtube', ''),
        'video_title': feat['video_title'],
        'section_title': feat['section_title'],
        'section_text': feat['section_text'],
        'channel_url': feat['channel_url'],
        'current_thumbnail_url': feat['thumbnail_url'] if feat['thumbnail_is_custom'] else '',
        'preview_thumbnail_url': feat['thumbnail_url'],
    }


def save_home_youtube_feature(cleaned_data, thumbnail_file=None, remove_thumbnail=False):
    ensure_home_youtube_blocks()

    def set_value(key, value):
        block = ContentBlock.objects.get(key=key)
        block.value = value or ''
        block.is_active = True
        block.save(update_fields=['value', 'is_active', 'updated_at'])

    video_url = (cleaned_data.get('video_url') or '').strip()
    set_value('home_youtube_video_url', video_url)
    set_value('home_youtube_video_title', cleaned_data.get('video_title', ''))
    set_value('home_youtube_section_title', cleaned_data.get('section_title', ''))
    set_value('home_youtube_section_text', cleaned_data.get('section_text', ''))
    set_value('home_youtube_channel_url', cleaned_data.get('channel_url', ''))

    thumb_block = ContentBlock.objects.get(key='home_youtube_thumbnail')
    if remove_thumbnail and thumb_block.image:
        thumb_block.image.delete(save=False)
        thumb_block.image = None
        thumb_block.save(update_fields=['image', 'updated_at'])
    elif thumbnail_file:
        if thumb_block.image:
            thumb_block.image.delete(save=False)
        thumb_block.image = thumbnail_file
        thumb_block.block_type = ContentBlock.BlockType.IMAGE
        thumb_block.is_active = True
        thumb_block.save(update_fields=['image', 'block_type', 'is_active', 'updated_at'])

    legacy = ContentBlock.objects.filter(key='featured_youtube').first()
    if legacy and video_url:
        legacy.value = ''
        legacy.save(update_fields=['value', 'updated_at'])


def migrate_legacy_featured_youtube():
    """Copy old embed URL block into home_youtube_video_url as watch URL."""
    ensure_home_youtube_blocks()
    legacy = ContentBlock.objects.filter(key='featured_youtube').first()
    home = ContentBlock.objects.filter(key='home_youtube_video_url').first()
    if not legacy or not legacy.value.strip():
        return
    if home and home.value.strip():
        return
    vid = youtube_video_id(legacy.value)
    if vid and home:
        home.value = f'https://www.youtube.com/watch?v={vid}'
        home.save(update_fields=['value', 'updated_at'])
