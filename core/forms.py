from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django.utils.text import slugify

from .models import (
    ContactMessage,
    ContentBlock,
    PastorProfile,
    Question,
    QuestionCategory,
    Resource,
)

User = get_user_model()
from .utils import youtube_embed_url, youtube_video_id, youtube_watch_url


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs['class'] = 'list-unstyled'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'form-control'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = css
                field.widget.attrs.setdefault('rows', 4)
            else:
                field.widget.attrs['class'] = css


class QuestionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Question
        fields = ['asker_name', 'asker_email', 'category', 'subject', 'question_text']
        widgets = {
            'subject': forms.TextInput(),
            'question_text': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asker_name'].label = _('Your name')
        self.fields['asker_email'].label = _('Email')
        self.fields['category'].label = _('Topic')
        self.fields['subject'].label = _('Subject')
        self.fields['question_text'].label = _('Your question')
        self.fields['subject'].widget.attrs['placeholder'] = _(
            'Brief summary of your situation...'
        )
        self.fields['question_text'].widget.attrs['placeholder'] = _(
            'Share what you are going through. You are not alone — '
            'we will respond with care and biblical guidance.'
        )
        self.fields['category'].queryset = QuestionCategory.objects.filter(is_active=True)
        self.fields['category'].empty_label = _('Choose a topic (optional)')
        self.fields['category'].required = False


class ContactForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['full_name', 'email', 'whatsapp_phone', 'message']
        labels = {
            'full_name': _('Full names'),
            'email': _('Email'),
            'whatsapp_phone': _('WhatsApp phone number'),
            'message': _('Your message'),
        }
        widgets = {
            'full_name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'whatsapp_phone': forms.TextInput(
                attrs={'autocomplete': 'tel', 'inputmode': 'tel'}
            ),
            'message': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['full_name'].widget.attrs['placeholder'] = _('Your full name')
        self.fields['email'].widget.attrs['placeholder'] = _('you@example.com (optional)')
        self.fields['whatsapp_phone'].widget.attrs['placeholder'] = _('e.g. 0783558316')
        self.fields['message'].widget.attrs['placeholder'] = _(
            'Write your message here — how can the pastor help you?'
        )

    def clean_message(self):
        message = (self.cleaned_data.get('message') or '').strip()
        if not message:
            raise forms.ValidationError(_('Please enter your message.'))
        return message

    def clean_whatsapp_phone(self):
        phone = (self.cleaned_data.get('whatsapp_phone') or '').strip()
        if not phone:
            raise forms.ValidationError(_('WhatsApp phone number is required.'))
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 9:
            raise forms.ValidationError(
                _('Enter a valid Rwanda phone number (e.g. 0783558316).')
            )
        return phone


class ResourceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Resource
        fields = [
            'title',
            'description',
            'resource_type',
            'youtube_url',
            'external_url',
            'file',
            'thumbnail',
            'is_published',
            'is_featured',
        ]
        help_texts = {
            'thumbnail': 'Optional custom cover. Leave empty to use the YouTube thumbnail.',
            'youtube_url': 'Full YouTube watch URL for this video.',
        }


class AnswerQuestionForm(StyledFormMixin, forms.ModelForm):
    recommended_resources = forms.ModelMultipleChoiceField(
        queryset=Resource.objects.filter(is_published=True).order_by('title'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Recommended resources',
        help_text='Select sermons, PDFs, or other published resources to suggest.',
    )

    class Meta:
        model = Question
        fields = [
            'answer_text',
            'answer_youtube_url',
            'answer_youtube_thumbnail',
            'is_public',
            'is_featured',
            'status',
        ]
        widgets = {
            'answer_text': forms.Textarea(
                attrs={
                    'rows': 6,
                    'placeholder': 'Write a text answer (optional if you add a video or resources)...',
                }
            ),
            'answer_youtube_url': forms.URLInput(
                attrs={'placeholder': 'https://www.youtube.com/watch?v=...'}
            ),
            'status': forms.HiddenInput(),
        }
        help_texts = {
            'answer_youtube_url': 'Paste a YouTube link for a video answer.',
            'answer_youtube_thumbnail': 'Optional custom cover (16:9). Leave empty to use the YouTube thumbnail.',
            'answer_text': 'Optional written explanation.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['recommended_resources'].initial = (
                self.instance.recommended_resources.all()
            )

    def clean_answer_youtube_url(self):
        url = (self.cleaned_data.get('answer_youtube_url') or '').strip()
        if not url:
            return ''
        if not youtube_video_id(url):
            raise forms.ValidationError(
                'Enter a valid YouTube URL (youtube.com/watch, youtu.be, or /shorts/).'
            )
        return youtube_watch_url(url)

    def clean(self):
        cleaned = super().clean()
        answer_text = (cleaned.get('answer_text') or '').strip()
        answer_youtube = (cleaned.get('answer_youtube_url') or '').strip()
        recommended = cleaned.get('recommended_resources')

        if not answer_text and not answer_youtube and not recommended:
            raise forms.ValidationError(
                'Provide at least one answer: text, a YouTube link, or recommended resources.'
            )
        if cleaned.get('is_featured') and not cleaned.get('is_public'):
            cleaned['is_featured'] = False
        return cleaned


class HomeYouTubeFeatureForm(StyledFormMixin, forms.Form):
    video_url = forms.URLField(
        label='Featured YouTube video URL',
        required=False,
        widget=forms.URLInput(
            attrs={'placeholder': 'https://www.youtube.com/watch?v=...'},
        ),
        help_text='Paste a YouTube link (e.g. https://youtu.be/qJjcI2wfuqo). The real video thumbnail is loaded from YouTube automatically.',
    )
    video_title = forms.CharField(
        label='Video title (optional)',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Sunday service — Faith in Christ'}),
    )
    thumbnail = forms.ImageField(
        label='Custom thumbnail (optional)',
        required=False,
        help_text='Upload JPG/PNG to override the YouTube thumbnail. Leave empty to use YouTube.',
    )
    remove_thumbnail = forms.BooleanField(
        label='Remove custom thumbnail (use YouTube image)',
        required=False,
    )
    section_title = forms.CharField(
        label='Section heading',
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Latest from YouTube'}),
    )
    section_text = forms.CharField(
        label='Section description',
        widget=forms.Textarea(attrs={'rows': 4}),
    )
    channel_url = forms.URLField(
        label='YouTube channel / Visit button link',
        widget=forms.URLInput(
            attrs={'placeholder': 'https://www.youtube.com/@INZIRAYUBUGINGOTV/videos'},
        ),
    )
    youtube_page_video_url = forms.URLField(
        label='YouTube page featured video URL',
        required=False,
        widget=forms.URLInput(
            attrs={'placeholder': 'https://youtu.be/RXrvatSzY8I'},
        ),
        help_text='Large featured card on /youtube/ — uses the real YouTube thumbnail.',
    )
    youtube_page_video_title = forms.CharField(
        label='YouTube page featured title (optional)',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'The Power of the Cross'}),
    )
    youtube_page_video_description = forms.CharField(
        label='YouTube page featured description (optional)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )

    def clean_video_url(self):
        url = (self.cleaned_data.get('video_url') or '').strip()
        if url and not youtube_video_id(url):
            raise forms.ValidationError(
                'Enter a valid YouTube URL (youtube.com or youtu.be).',
            )
        return url

    def clean_youtube_page_video_url(self):
        url = (self.cleaned_data.get('youtube_page_video_url') or '').strip()
        if url and not youtube_video_id(url):
            raise forms.ValidationError(
                'Enter a valid YouTube URL (youtube.com or youtu.be).',
            )
        return url

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('remove_thumbnail') and cleaned.get('thumbnail'):
            self.add_error(
                'thumbnail',
                'Clear the file upload or uncheck “Remove custom thumbnail”.',
            )
        return cleaned


def _make_site_settings_form():
    from .site_settings import build_site_settings_form_class

    base = build_site_settings_form_class()

    class SiteSettingsForm(StyledFormMixin, base):
        def clean_home_youtube_video_url(self):
            url = (self.cleaned_data.get('home_youtube_video_url') or '').strip()
            if url and not youtube_video_id(url):
                raise forms.ValidationError('Enter a valid YouTube URL.')
            return url

        def clean_youtube_featured_video_url(self):
            url = (self.cleaned_data.get('youtube_featured_video_url') or '').strip()
            if url and not youtube_video_id(url):
                raise forms.ValidationError('Enter a valid YouTube URL.')
            return url

        def clean(self):
            cleaned = super().clean()
            if cleaned.get('remove_home_thumbnail') and cleaned.get('home_youtube_thumbnail'):
                self.add_error(
                    'home_youtube_thumbnail',
                    'Clear the upload or uncheck remove thumbnail.',
                )
            return cleaned

    return SiteSettingsForm


SiteSettingsForm = _make_site_settings_form()


class ContentBlockForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContentBlock
        fields = ['key', 'label', 'block_type', 'value', 'image', 'is_active']
        widgets = {
            'value': forms.Textarea(attrs={'rows': 3}),
            'key': forms.TextInput(attrs={'placeholder': 'hero_title'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['key'].disabled = True


class QuestionFilterForm(StyledFormMixin, forms.Form):
    q = forms.CharField(
        label='Search',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Name, subject, question, answer…'}),
    )
    status = forms.ChoiceField(
        label='Status',
        required=False,
        choices=[
            ('', 'All statuses'),
            ('pending', 'Pending'),
            ('answered', 'Answered'),
            ('archived', 'Archived'),
        ],
    )
    category = forms.ChoiceField(
        label='Category',
        required=False,
        choices=[('', 'All categories')],
    )
    visibility = forms.ChoiceField(
        label='Public Q&A',
        required=False,
        choices=[
            ('', 'Any visibility'),
            ('public', 'Published on site'),
            ('private', 'Not published'),
            ('featured', 'Featured on Q&A page'),
        ],
    )
    year = forms.ChoiceField(label='Year', required=False, choices=[('', 'Any year')])
    date_from = forms.DateField(
        label='From date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        label='To date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    email = forms.CharField(
        label='Email',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'filter@email.com'}),
    )

    def __init__(self, *args, year_choices=None, category_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if year_choices:
            self.fields['year'].choices = [('', 'Any year')] + [
                (str(y), str(y)) for y in year_choices
            ]
        if category_choices:
            self.fields['category'].choices = [('', 'All categories')] + [
                (cat.slug, cat.name) for cat in category_choices
            ]


class MessageFilterForm(StyledFormMixin, forms.Form):
    q = forms.CharField(
        label='Search',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Name, message, phone, notes…'}),
    )
    status = forms.ChoiceField(
        label='Status',
        required=False,
        choices=[
            ('', 'All statuses'),
            ('pending', 'Pending'),
            ('read', 'Read'),
            ('replied', 'Replied'),
            ('archived', 'Archived'),
        ],
    )
    year = forms.ChoiceField(label='Year', required=False, choices=[('', 'Any year')])
    date_from = forms.DateField(
        label='From date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        label='To date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    phone = forms.CharField(
        label='WhatsApp / phone',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 078…'}),
    )
    email = forms.CharField(
        label='Email',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'filter@email.com'}),
    )

    def __init__(self, *args, year_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if year_choices:
            self.fields['year'].choices = [('', 'Any year')] + [
                (str(y), str(y)) for y in year_choices
            ]


class NotificationFilterForm(StyledFormMixin, forms.Form):
    q = forms.CharField(
        label='Search',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Name, title, message…'}),
    )
    type = forms.ChoiceField(
        label='Type',
        required=False,
        choices=[('', 'All types')],
    )
    status = forms.ChoiceField(
        label='Status',
        required=False,
        choices=[
            ('', 'All'),
            ('unread', 'Unread only'),
            ('read', 'Read only'),
        ],
    )
    year = forms.ChoiceField(label='Year', required=False, choices=[('', 'Any year')])
    date_from = forms.DateField(
        label='From date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        label='To date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    phone = forms.CharField(
        label='Phone / WhatsApp',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 078…'}),
    )
    email = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'filter@email.com'}),
    )

    def __init__(self, *args, type_choices=None, year_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if type_choices:
            self.fields['type'].choices = [('', 'All types')] + list(type_choices)
        if year_choices:
            self.fields['year'].choices = [('', 'Any year')] + [
                (str(y), str(y)) for y in year_choices
            ]


class QuestionCategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = QuestionCategory
        fields = ['name', 'slug', 'description', 'icon', 'sort_order', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'icon': forms.TextInput(attrs={'placeholder': 'bi-heart'}),
            'slug': forms.TextInput(attrs={'placeholder': 'auto-from-name'}),
        }

    def clean_slug(self):
        slug = (self.cleaned_data.get('slug') or '').strip()
        name = (self.cleaned_data.get('name') or '').strip()
        if not slug and name:
            slug = slugify(name)[:90] or 'category'
        if not slug:
            raise forms.ValidationError('Slug is required.')
        qs = QuestionCategory.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This slug is already in use.')
        return slug


class ContactMessageForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['status', 'admin_notes']
        widgets = {
            'admin_notes': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Private notes for your follow-up...'}),
        }


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['class'] = 'form-control'


class DashboardUserProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'Email',
        }


class DashboardUsernameForm(StyledFormMixin, forms.Form):
    username = forms.CharField(
        max_length=150,
        label='Username',
        help_text='Used to sign in to the dashboard.',
    )
    current_password = forms.CharField(
        label='Current password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
        help_text='Required to change your username.',
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['username'].initial = user.username

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise ValidationError('Username is required.')
        qs = User.objects.filter(username__iexact=username)
        if qs.exclude(pk=self.user.pk).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('current_password')
        if password and not self.user.check_password(password):
            self.add_error('current_password', 'Current password is incorrect.')
        return cleaned


class DashboardPasswordChangeForm(StyledFormMixin, forms.Form):
    current_password = forms.CharField(
        label='Current password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )
    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    new_password2 = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        password = self.cleaned_data.get('current_password')
        if password and not self.user.check_password(password):
            raise ValidationError('Current password is incorrect.')
        return password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            self.add_error('new_password2', 'Passwords do not match.')
        if p1:
            validate_password(p1, self.user)
        return cleaned


class PastorProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = PastorProfile
        fields = ['title', 'phone', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'title': 'Title / role label',
            'phone': 'Phone (optional)',
        }
