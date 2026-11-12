"""Type-specific resource forms for the dashboard."""

from django import forms

from .category_helpers import topic_choices_for_form
from .forms import StyledFormMixin
from .models import Resource


class _ResourceFormBase(StyledFormMixin, forms.ModelForm):
    """Sets resource_type on save."""

    resource_type_value = None
    require_category = False

    class Meta:
        model = Resource
        fields = ['title', 'description', 'category', 'is_published', 'is_featured']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = topic_choices_for_form()
        self.fields['category'].label = 'Spiritual topic'
        self.fields['category'].empty_label = '— Choose a topic —'
        self.fields['category'].help_text = (
            'Same topics as Q&A — helps visitors find related teachings.'
        )

    def clean(self):
        cleaned = super().clean()
        if self.require_category and not cleaned.get('category'):
            self.add_error(
                'category',
                'Choose a topic so this teaching appears in the right browse filters.',
            )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.resource_type_value:
            instance.resource_type = self.resource_type_value
        if commit:
            instance.save()
        return instance


class VideoResourceForm(_ResourceFormBase):
    resource_type_value = Resource.ResourceType.VIDEO
    require_category = True

    class Meta(_ResourceFormBase.Meta):
        fields = _ResourceFormBase.Meta.fields + ['youtube_url', 'thumbnail']
        help_texts = {
            'youtube_url': 'Paste the full YouTube watch link.',
            'thumbnail': 'Optional custom cover (16:9). Leave empty to use the YouTube thumbnail.',
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('youtube_url'):
            self.add_error('youtube_url', 'YouTube URL is required for video resources.')
        return cleaned


class AudioResourceForm(_ResourceFormBase):
    resource_type_value = Resource.ResourceType.AUDIO
    require_category = True

    class Meta(_ResourceFormBase.Meta):
        fields = _ResourceFormBase.Meta.fields + ['youtube_url', 'thumbnail']
        help_texts = {
            'youtube_url': 'YouTube link for this audio message or podcast episode.',
            'thumbnail': 'Optional custom cover. Leave empty to use the YouTube thumbnail.',
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('youtube_url'):
            self.add_error(
                'youtube_url',
                'YouTube URL is required — audio is published via YouTube.',
            )
        return cleaned


class PdfResourceForm(_ResourceFormBase):
    resource_type_value = Resource.ResourceType.PDF

    class Meta(_ResourceFormBase.Meta):
        fields = _ResourceFormBase.Meta.fields + ['file', 'external_url', 'thumbnail']
        help_texts = {
            'file': 'Upload a PDF document.',
            'external_url': 'Or link to a PDF hosted elsewhere.',
            'thumbnail': 'Optional preview image.',
        }

    def clean(self):
        cleaned = super().clean()
        has_file = cleaned.get('file') or (self.instance.pk and self.instance.file)
        has_url = cleaned.get('external_url')
        if not has_file and not has_url:
            raise forms.ValidationError(
                'Provide a PDF file upload or an external PDF link.'
            )
        return cleaned


class SlideResourceForm(_ResourceFormBase):
    resource_type_value = Resource.ResourceType.SLIDE

    class Meta(_ResourceFormBase.Meta):
        fields = _ResourceFormBase.Meta.fields + ['file', 'external_url', 'thumbnail']
        help_texts = {
            'file': 'Upload slides (PDF, PPTX, etc.).',
            'external_url': 'Or link to slides online.',
            'thumbnail': 'Optional preview image.',
        }

    def clean(self):
        cleaned = super().clean()
        has_file = cleaned.get('file') or (self.instance.pk and self.instance.file)
        has_url = cleaned.get('external_url')
        if not has_file and not has_url:
            raise forms.ValidationError(
                'Provide a file upload or an external link for slides.'
            )
        return cleaned


class SermonResourceForm(_ResourceFormBase):
    resource_type_value = Resource.ResourceType.SERMON

    class Meta(_ResourceFormBase.Meta):
        fields = _ResourceFormBase.Meta.fields + [
            'youtube_url',
            'file',
            'external_url',
            'thumbnail',
        ]
        help_texts = {
            'youtube_url': 'Optional YouTube link for this sermon.',
            'file': 'Optional audio/video file upload.',
            'external_url': 'Optional external link.',
            'thumbnail': 'Optional custom cover. Uses YouTube thumbnail when a link is set.',
        }

    def clean(self):
        cleaned = super().clean()
        has_yt = cleaned.get('youtube_url')
        has_file = cleaned.get('file') or (self.instance.pk and self.instance.file)
        has_url = cleaned.get('external_url')
        if not has_yt and not has_file and not has_url:
            raise forms.ValidationError(
                'Add at least one: YouTube link, file upload, or external URL.'
            )
        return cleaned


RESOURCE_TYPE_CONFIG = {
    'video': {
        'form': VideoResourceForm,
        'label': 'Video',
        'icon': 'bi-camera-reels',
        'color': '#dc3545',
        'description': 'YouTube sermons and teachings (YouTube thumbnail by default).',
    },
    'audio': {
        'form': AudioResourceForm,
        'label': 'Audio',
        'icon': 'bi-headphones',
        'color': '#198754',
        'description': 'Audio messages on YouTube (YouTube thumbnail by default).',
    },
    'pdf': {
        'form': PdfResourceForm,
        'label': 'PDF',
        'icon': 'bi-filetype-pdf',
        'color': '#b45309',
        'description': 'Study guides, notes, and printable materials.',
    },
    'slides': {
        'form': SlideResourceForm,
        'label': 'Teaching slides',
        'icon': 'bi-easel',
        'color': '#0d6efd',
        'description': 'Presentation slides and visual teaching aids.',
    },
    'sermon': {
        'form': SermonResourceForm,
        'label': 'Sermon',
        'icon': 'bi-mic',
        'color': '#0A2F1F',
        'description': 'General sermon — video, audio, or file.',
    },
}


def get_resource_type_slug(resource):
    mapping = {
        Resource.ResourceType.VIDEO: 'video',
        Resource.ResourceType.AUDIO: 'audio',
        Resource.ResourceType.PDF: 'pdf',
        Resource.ResourceType.SLIDE: 'slides',
        Resource.ResourceType.SERMON: 'sermon',
    }
    return mapping.get(resource.resource_type, 'sermon')


def get_form_for_resource(resource=None, resource_type_slug=None):
    if resource:
        slug = get_resource_type_slug(resource)
    else:
        slug = resource_type_slug
    config = RESOURCE_TYPE_CONFIG.get(slug)
    if not config:
        return None, None
    return slug, config['form']
