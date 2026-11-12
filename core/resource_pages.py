"""Public resource listing page configuration."""

from django.utils.translation import gettext_lazy as _

RESOURCE_PAGE_CONFIG = {
    'pdf': {
        'title': _('PDF Resources'),
        'subtitle': _(
            'Study guides, class handouts, and printable materials to grow in Scripture.'
        ),
        'badge': _('PDF'),
        'icon': 'bi-filetype-pdf',
        'accent': '#b45309',
        'accent_soft': 'rgba(180, 83, 9, 0.12)',
        'hero_from': '#0A2F1F',
        'hero_via': '#5c3d0a',
        'hero_to': '#92400e',
        'dashboard_slug': 'pdf',
        'empty_icon': 'bi-file-earmark-pdf',
    },
    'slides': {
        'title': _('Teaching Slides'),
        'subtitle': _(
            'Presentation slides and visual aids for Bible studies and teaching sessions.'
        ),
        'badge': _('Slides'),
        'icon': 'bi-easel',
        'accent': '#0d6efd',
        'accent_soft': 'rgba(13, 110, 253, 0.12)',
        'hero_from': '#0A2F1F',
        'hero_via': '#1e3a5f',
        'hero_to': '#0d47a1',
        'dashboard_slug': 'slides',
        'empty_icon': 'bi-easel2',
    },
    'sermon': {
        'title': _('Sermons'),
        'subtitle': _('Sermon recordings, notes, and related teaching resources.'),
        'badge': _('Sermon'),
        'icon': 'bi-mic',
        'accent': '#0A2F1F',
        'accent_soft': 'rgba(10, 47, 31, 0.1)',
        'hero_from': '#0A2F1F',
        'hero_via': '#1A4A2F',
        'hero_to': '#0e3822',
        'dashboard_slug': 'sermon',
        'empty_icon': 'bi-mic',
    },
}
