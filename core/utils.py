import re
from urllib.parse import parse_qs, quote, urlparse

from django.conf import settings
from django.utils.translation import gettext as _


_YOUTUBE_ID_RE = re.compile(
    r'(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/|v/|shorts/|live/)|youtu\.be/)([\w-]{11})',
    re.IGNORECASE,
)

def normalize_rwanda_whatsapp(number: str) -> str:
    """Convert local format 0783558316 to international 250783558316."""
    digits = ''.join(c for c in number if c.isdigit())
    if digits.startswith('250'):
        return digits
    if digits.startswith('0'):
        return '250' + digits[1:]
    if len(digits) == 9:
        return '250' + digits
    return digits


def _admin_whatsapp_number() -> str:
    try:
        from .site_settings import get_public_contact
        return get_public_contact()['whatsapp'] or settings.ADMIN_WHATSAPP_NUMBER
    except Exception:
        return settings.ADMIN_WHATSAPP_NUMBER


def whatsapp_link(message: str, phone: str | None = None) -> str:
    phone = normalize_rwanda_whatsapp(phone or _admin_whatsapp_number())
    return f'https://wa.me/{phone}?text={quote(message)}'


def youtube_video_id(url: str) -> str | None:
    if not url:
        return None
    match = _YOUTUBE_ID_RE.search(url)
    if match:
        return match.group(1)
    parsed = urlparse(url)
    if parsed.hostname and 'youtube' in parsed.hostname:
        qs = parse_qs(parsed.query)
        if qs.get('v'):
            return qs['v'][0][:11]
    return None


def youtube_embed_url(url: str, *, autoplay: bool = False) -> str:
    video_id = youtube_video_id(url)
    if not video_id:
        return ''
    params = 'rel=0&modestbranding=1'
    if autoplay:
        params += '&autoplay=1'
    return f'https://www.youtube.com/embed/{video_id}?{params}'


def youtube_watch_url(url: str) -> str:
    video_id = youtube_video_id(url)
    if video_id:
        return f'https://www.youtube.com/watch?v={video_id}'
    return url or ''


def youtube_thumbnail_url(video_id: str, quality: str = 'hqdefault') -> str:
    """Public YouTube CDN thumbnail (hqdefault always exists; maxresdefault may not)."""
    if not video_id:
        return ''
    return f'https://img.youtube.com/vi/{video_id}/{quality}.jpg'


def youtube_thumbnail_urls(video_id: str) -> dict[str, str]:
    """Best-effort thumbnail URLs (use maxres in <img> with hqdefault onerror fallback)."""
    if not video_id:
        return {}
    return {
        'maxres': youtube_thumbnail_url(video_id, 'maxresdefault'),
        'hq': youtube_thumbnail_url(video_id, 'hqdefault'),
        'mq': youtube_thumbnail_url(video_id, 'mqdefault'),
    }


def contact_inbound_message(contact) -> str:
    """Text sent *to* the pastor (0783558316) when someone uses Get in Touch."""
    email_line = contact.email if contact.email else _('(not provided)')
    body = (contact.message or '').strip() or _('(no message)')
    return (
        _('New Get in Touch message (Inzira y\'ubugingo)') + '\n'
        + _('Full name: %(name)s') % {'name': contact.full_name} + '\n'
        + _('WhatsApp: %(phone)s') % {'phone': contact.whatsapp_phone} + '\n'
        + _('Email: %(email)s') % {'email': email_line} + '\n'
        + _('Message: %(message)s') % {'message': body}
    )


def contact_reply_message(contact) -> str:
    """Pre-filled text when the pastor replies to the visitor on WhatsApp."""
    return _(
        'Hello %(name)s, thank you for contacting Inzira y\'ubugingo. '
        'I received your message and wanted to follow up with you.'
    ) % {'name': contact.full_name}


def contact_reply_email_url(contact) -> str:
    """mailto: link to reply by email when the visitor provided an address."""
    from urllib.parse import quote

    if not (contact.email or '').strip():
        return ''
    subject = quote(_("Re: Your message to Inzira y'ubugingo"))
    body = quote(
        _(
            'Hello %(name)s,\n\n'
            'Thank you for contacting Inzira y\'ubugingo. '
            'I received your message and am following up with you.\n\n'
            'Blessings,\n'
            'Pastor'
        ) % {'name': contact.full_name}
    )
    return f'mailto:{contact.email.strip()}?subject={subject}&body={body}'


def pastor_whatsapp_link(message: str) -> str:
    """Open WhatsApp chat with the pastor number from site settings."""
    return whatsapp_link(message, phone=_admin_whatsapp_number())


def reply_to_visitor_whatsapp_link(contact) -> str:
    """Open WhatsApp chat with the visitor's number so the pastor can reply."""
    return whatsapp_link(contact_reply_message(contact), phone=contact.whatsapp_phone)


# Backwards compatibility
contact_whatsapp_message = contact_inbound_message
