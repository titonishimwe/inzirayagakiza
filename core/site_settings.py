"""Central site settings — ContentBlock keys grouped for the dashboard."""

from django import forms

from .home_youtube import ensure_home_youtube_blocks, save_home_youtube_feature
from .models import ContentBlock
from .utils import youtube_video_id
from .youtube_page import ensure_youtube_page_blocks, save_youtube_page_featured

DEFAULT_HERO_VERSE_TEXT = (
    'All Scripture is God-breathed and is useful for teaching, rebuking, '
    'correcting and training in righteousness, so that the servant of God '
    'may be thoroughly equipped for every good work.'
)
DEFAULT_HERO_VERSE_REFERENCE = '2 Timothy 3:16-17'

DEFAULT_QA_BANNER_TITLE = 'Frequently Asked Bible Questions'
DEFAULT_QA_BANNER_SUBTITLE = (
    'Clear, Scripture-based answers to questions people ask most often about faith and life.'
)

# (key, default_value, block_type)
CORE_SITE_BLOCKS = [
    ('hero_tagline', 'Teaching Gospel to the Nation', ContentBlock.BlockType.TEXT),
    ('hero_title', "Inzira y'ubugingo", ContentBlock.BlockType.TEXT),
    (
        'hero_subtitle',
        'Equipping believers, spreading truth, and transforming lives through the Word of God.',
        ContentBlock.BlockType.TEXT,
    ),
    ('hero_verse_text', DEFAULT_HERO_VERSE_TEXT, ContentBlock.BlockType.TEXT),
    ('hero_verse_reference', DEFAULT_HERO_VERSE_REFERENCE, ContentBlock.BlockType.TEXT),
    ('qa_banner_title', DEFAULT_QA_BANNER_TITLE, ContentBlock.BlockType.TEXT),
    ('qa_banner_subtitle', DEFAULT_QA_BANNER_SUBTITLE, ContentBlock.BlockType.TEXT),
    ('qa_featured_heading', 'Top questions', ContentBlock.BlockType.TEXT),
    ('qa_verse_text', DEFAULT_HERO_VERSE_TEXT, ContentBlock.BlockType.TEXT),
    ('qa_verse_reference', DEFAULT_HERO_VERSE_REFERENCE, ContentBlock.BlockType.TEXT),
    ('featured_youtube', '', ContentBlock.BlockType.URL),
    (
        'support_intro',
        (
            "Your generous support helps Inzira y'ubugingo share the Gospel through "
            'video teachings, audio messages, printed resources, and community outreach.'
        ),
        ContentBlock.BlockType.TEXT,
    ),
    ('support_mtn_momo', '', ContentBlock.BlockType.TEXT),
    ('support_airtel_money', '', ContentBlock.BlockType.TEXT),
    ('support_bk_name', "Inzira y'ubugingo", ContentBlock.BlockType.TEXT),
    ('support_bk_number', '', ContentBlock.BlockType.TEXT),
    ('support_equity_name', "Inzira y'ubugingo", ContentBlock.BlockType.TEXT),
    ('support_equity_number', '', ContentBlock.BlockType.TEXT),
]

_CONTACT_SOCIAL_DEFAULTS = [
    ('contact_whatsapp', '0783558316', ContentBlock.BlockType.TEXT),
    ('contact_email', 'hello@inzirayubugingo.rw', ContentBlock.BlockType.TEXT),
    ('contact_phone', '+250 788 123 456', ContentBlock.BlockType.TEXT),
    ('contact_address', 'Kigali, Rwanda', ContentBlock.BlockType.TEXT),
    ('youtube_channel_url', 'https://www.youtube.com/@INZIRAYUBUGINGOTV/videos', ContentBlock.BlockType.URL),
    ('social_facebook', '', ContentBlock.BlockType.URL),
    ('social_instagram', '', ContentBlock.BlockType.URL),
    ('social_whatsapp', '', ContentBlock.BlockType.URL),
    ('social_tiktok', '', ContentBlock.BlockType.URL),
    ('footer_about', (
        "Teaching the Gospel to the Nation with clarity and truth. We provide resources, "
        'biblical teachings, and community support to grow in faith.'
    ), ContentBlock.BlockType.TEXT),
]

SITE_SETTINGS_SECTIONS = [
    {
        'id': 'homepage',
        'title': 'Homepage',
        'icon': 'bi-house-door-fill',
        'description': (
            'Hero banner text and the Bible verse card on the right. '
            'Statistics (sermons, audio, PDFs) are counted automatically from published resources.'
        ),
        'fields': [
            {'key': 'hero_tagline', 'label': 'Tagline', 'type': 'text', 'rows': 1,
             'help': 'Short line above the main title.'},
            {'key': 'hero_title', 'label': 'Main title', 'type': 'text', 'rows': 1},
            {'key': 'hero_subtitle', 'label': 'Subtitle / description', 'type': 'textarea', 'rows': 3},
            {'key': 'hero_verse_text', 'label': 'Hero verse text', 'type': 'textarea', 'rows': 5,
             'help': 'Scripture shown in the glass card on the homepage (quotes added automatically).'},
            {'key': 'hero_verse_reference', 'label': 'Hero verse reference', 'type': 'text', 'rows': 1,
             'help': 'e.g. 2 Timothy 3:16-17 — shown below the verse.'},
        ],
        'show_live_stats': True,
    },
    {
        'id': 'qa-page',
        'title': 'Q&A page (/qa/)',
        'icon': 'bi-chat-square-quote-fill',
        'description': (
            'Banner, featured section title, and the Scripture card shown on the public Q&A page. '
            'Mark individual questions as “Featured” in the Questions dashboard to fill the top list.'
        ),
        'fields': [
            {'key': 'qa_banner_title', 'label': 'Banner title', 'type': 'text', 'rows': 1},
            {'key': 'qa_banner_subtitle', 'label': 'Banner subtitle', 'type': 'textarea', 'rows': 2},
            {'key': 'qa_featured_heading', 'label': 'Featured section heading', 'type': 'text', 'rows': 1,
             'help': 'e.g. “Top 20 questions” — shown above the featured grid.'},
            {'key': 'qa_verse_text', 'label': 'Scripture card text', 'type': 'textarea', 'rows': 4},
            {'key': 'qa_verse_reference', 'label': 'Scripture reference', 'type': 'text', 'rows': 1},
        ],
    },
    {
        'id': 'contact',
        'title': 'Contact information',
        'icon': 'bi-telephone-fill',
        'description': 'Shown on Get in Touch, footer, and WhatsApp notifications.',
        'fields': [
            {'key': 'contact_whatsapp', 'label': 'Pastor WhatsApp number', 'type': 'text', 'rows': 1,
             'help': 'Rwanda format, e.g. 0783558316 — used for inbound contact alerts.'},
            {'key': 'contact_email', 'label': 'Public email', 'type': 'text', 'rows': 1},
            {'key': 'contact_phone', 'label': 'Public phone', 'type': 'text', 'rows': 1},
            {'key': 'contact_address', 'label': 'Location / address', 'type': 'text', 'rows': 1},
        ],
    },
    {
        'id': 'social',
        'title': 'Social media & YouTube channel',
        'icon': 'bi-share-fill',
        'description': 'Footer icons and “Visit channel” links across the site.',
        'fields': [
            {'key': 'youtube_channel_url', 'label': 'YouTube channel URL', 'type': 'url', 'rows': 1},
            {'key': 'social_facebook', 'label': 'Facebook page URL', 'type': 'url', 'rows': 1},
            {'key': 'social_instagram', 'label': 'Instagram URL', 'type': 'url', 'rows': 1},
            {'key': 'social_whatsapp', 'label': 'WhatsApp community / channel link', 'type': 'url', 'rows': 1},
            {'key': 'social_tiktok', 'label': 'TikTok URL', 'type': 'url', 'rows': 1},
        ],
    },
    {
        'id': 'homepage-youtube',
        'title': 'Homepage featured video',
        'icon': 'bi-play-btn-fill',
        'description': 'Video card on the homepage (thumbnail from YouTube or custom upload).',
        'fields': [
            {'key': 'home_youtube_video_url', 'label': 'YouTube video URL', 'type': 'url', 'rows': 1,
             'help': 'youtu.be or youtube.com/watch link.'},
            {'key': 'home_youtube_video_title', 'label': 'Video title (optional overlay)', 'type': 'text', 'rows': 1},
            {'key': 'home_youtube_section_title', 'label': 'Section heading', 'type': 'text', 'rows': 1},
            {'key': 'home_youtube_section_text', 'label': 'Section description', 'type': 'textarea', 'rows': 3},
            {'key': 'home_youtube_channel_url', 'label': '“Visit channel” button URL', 'type': 'url', 'rows': 1},
        ],
        'extra': 'home_youtube_thumbnail',
    },
    {
        'id': 'youtube-page',
        'title': 'YouTube page (/youtube/)',
        'icon': 'bi-youtube',
        'description': (
            'Large featured teaching card at the top of the YouTube videos page. '
            'Title and description here always show on the public page when set.'
        ),
        'fields': [
            {'key': 'youtube_featured_video_url', 'label': 'Featured video URL', 'type': 'url', 'rows': 1,
             'help': 'youtu.be or youtube.com/watch link — thumbnail is taken from YouTube (or a matching resource).'},
            {'key': 'youtube_featured_video_title', 'label': 'Featured title', 'type': 'text', 'rows': 1,
             'help': 'Shown as the card headline on /youtube/.'},
            {'key': 'youtube_featured_video_description', 'label': 'Featured description', 'type': 'textarea', 'rows': 2,
             'help': 'Short text under the title on the featured card.'},
        ],
    },
    {
        'id': 'support',
        'title': 'Support Us modal',
        'icon': 'bi-heart-fill',
        'description': 'Payment details in the navbar “Support Us” popup.',
        'fields': [
            {'key': 'support_intro', 'label': 'Support message', 'type': 'textarea', 'rows': 4},
            {'key': 'support_mtn_momo', 'label': 'MTN Mobile Money number', 'type': 'text', 'rows': 1},
            {'key': 'support_airtel_money', 'label': 'Airtel Money number', 'type': 'text', 'rows': 1},
            {'key': 'support_bk_name', 'label': 'Bank of Kigali — account name', 'type': 'text', 'rows': 1},
            {'key': 'support_bk_number', 'label': 'Bank of Kigali — account number', 'type': 'text', 'rows': 1},
            {'key': 'support_equity_name', 'label': 'Equity Bank — account name', 'type': 'text', 'rows': 1},
            {'key': 'support_equity_number', 'label': 'Equity Bank — account number', 'type': 'text', 'rows': 1},
        ],
    },
    {
        'id': 'footer',
        'title': 'Footer',
        'icon': 'bi-layout-text-window-reverse',
        'description': 'Short about text in the site footer.',
        'fields': [
            {'key': 'footer_about', 'label': 'About paragraph', 'type': 'textarea', 'rows': 3},
        ],
    },
]


def ensure_all_site_blocks():
    for key, value, block_type in CORE_SITE_BLOCKS:
        ContentBlock.objects.get_or_create(
            key=key,
            defaults={
                'label': key.replace('_', ' ').title(),
                'block_type': block_type,
                'value': value if block_type != ContentBlock.BlockType.URL else '',
            },
        )
    for key, value, block_type in _CONTACT_SOCIAL_DEFAULTS:
        ContentBlock.objects.get_or_create(
            key=key,
            defaults={
                'label': key.replace('_', ' ').title(),
                'block_type': block_type,
                'value': value if block_type != ContentBlock.BlockType.URL else '',
            },
        )
    ensure_home_youtube_blocks()
    ensure_youtube_page_blocks()


def _block_value(key, default=''):
    try:
        block = ContentBlock.objects.get(key=key, is_active=True)
        if block.block_type == ContentBlock.BlockType.IMAGE:
            return ''
        return block.value or default
    except ContentBlock.DoesNotExist:
        return default


def get_site_settings_initial():
    ensure_all_site_blocks()
    initial = {}
    for section in SITE_SETTINGS_SECTIONS:
        for field in section['fields']:
            initial[field['key']] = _block_value(field['key'])
    from .home_youtube import home_youtube_form_initial
    from .youtube_page import youtube_page_featured_form_initial

    yt_home = home_youtube_form_initial()
    initial['home_youtube_video_url'] = yt_home.get('video_url', '')
    initial['home_youtube_video_title'] = yt_home.get('video_title', '')
    initial['home_youtube_section_title'] = yt_home.get('section_title', '')
    initial['home_youtube_section_text'] = yt_home.get('section_text', '')
    initial['home_youtube_channel_url'] = yt_home.get('channel_url', '')

    yt_page = youtube_page_featured_form_initial()
    initial['youtube_featured_video_url'] = yt_page.get('youtube_page_video_url', '')
    initial['youtube_featured_video_title'] = yt_page.get('youtube_page_video_title', '')
    initial['youtube_featured_video_description'] = yt_page.get(
        'youtube_page_video_description', '',
    )
    return initial


def build_site_settings_form_class():
    """Dynamically build the form class from SITE_SETTINGS_SECTIONS."""

    field_defs = {}
    for section in SITE_SETTINGS_SECTIONS:
        for spec in section['fields']:
            key = spec['key']
            ftype = spec['type']
            label = spec['label']
            help_text = spec.get('help', '')
            required = False
            if ftype == 'url':
                field_defs[key] = forms.URLField(
                    label=label, required=required, help_text=help_text,
                    widget=forms.URLInput(attrs={'class': 'form-control'}),
                )
            elif ftype == 'textarea':
                field_defs[key] = forms.CharField(
                    label=label, required=required, help_text=help_text,
                    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': spec.get('rows', 3)}),
                )
            else:
                field_defs[key] = forms.CharField(
                    label=label, required=required, help_text=help_text,
                    widget=forms.TextInput(attrs={'class': 'form-control'}),
                )

    field_defs['home_youtube_thumbnail'] = forms.ImageField(
        label='Custom homepage video thumbnail',
        required=False,
        help_text='Optional — leave empty to use the YouTube thumbnail.',
    )
    field_defs['remove_home_thumbnail'] = forms.BooleanField(
        label='Remove custom thumbnail (use YouTube image)',
        required=False,
    )

    return type(
        'SiteSettingsForm',
        (forms.Form,),
        field_defs,
    )


def save_site_settings(cleaned_data, thumbnail_file=None, remove_thumbnail=False):
    ensure_all_site_blocks()

    skip = {'home_youtube_thumbnail', 'remove_home_thumbnail'}
    for key, value in cleaned_data.items():
        if key in skip:
            continue
        try:
            block = ContentBlock.objects.get(key=key)
        except ContentBlock.DoesNotExist:
            continue
        if block.block_type == ContentBlock.BlockType.IMAGE:
            continue
        block.value = (value or '').strip() if value is not None else ''
        block.is_active = True
        block.save(update_fields=['value', 'is_active', 'updated_at'])

    home_payload = {
        'video_url': cleaned_data.get('home_youtube_video_url', ''),
        'video_title': cleaned_data.get('home_youtube_video_title', ''),
        'section_title': cleaned_data.get('home_youtube_section_title', ''),
        'section_text': cleaned_data.get('home_youtube_section_text', ''),
        'channel_url': cleaned_data.get('home_youtube_channel_url', '')
        or cleaned_data.get('youtube_channel_url', ''),
    }
    save_home_youtube_feature(
        home_payload,
        thumbnail_file=thumbnail_file,
        remove_thumbnail=remove_thumbnail,
    )
    save_youtube_page_featured({
        'youtube_page_video_url': cleaned_data.get('youtube_featured_video_url', ''),
        'youtube_page_video_title': cleaned_data.get('youtube_featured_video_title', ''),
        'youtube_page_video_description': cleaned_data.get(
            'youtube_featured_video_description', '',
        ),
    })


def sections_for_template(form, sections=None):
    """Attach bound form fields for Django templates (no dynamic form[key] syntax)."""
    sections = sections or SITE_SETTINGS_SECTIONS
    result = []
    for section in sections:
        fields = []
        for spec in section['fields']:
            key = spec['key']
            entry = {**spec, 'field': form[key] if key in form.fields else None}
            fields.append(entry)
        result.append({**section, 'fields': fields})
    return result


def get_public_contact():
    from django.conf import settings

    return {
        'whatsapp': _block_value('contact_whatsapp', settings.ADMIN_WHATSAPP_NUMBER),
        'email': _block_value('contact_email', 'hello@inzirayubugingo.rw'),
        'phone': _block_value('contact_phone', ''),
        'address': _block_value('contact_address', ''),
    }
