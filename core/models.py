from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PastorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pastor_profile',
    )
    title = models.CharField(max_length=120, blank=True, default='Pastor')
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class ContentBlock(TimeStampedModel):
    """Key-value site content managed from admin/dashboard."""

    class BlockType(models.TextChoices):
        TEXT = 'text', 'Text'
        NUMBER = 'number', 'Number'
        URL = 'url', 'URL'
        IMAGE = 'image', 'Image'

    key = models.SlugField(max_length=80, unique=True)
    label = models.CharField(max_length=120)
    block_type = models.CharField(
        max_length=20,
        choices=BlockType.choices,
        default=BlockType.TEXT,
    )
    value = models.TextField(blank=True)
    image = models.ImageField(upload_to='content/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['label']

    def __str__(self):
        return self.label


class Resource(TimeStampedModel):
    class ResourceType(models.TextChoices):
        VIDEO = 'video', 'Video Sermon'
        AUDIO = 'audio', 'Audio Sermon'
        PDF = 'pdf', 'PDF'
        SLIDE = 'slide', 'Teaching Slides'
        SERMON = 'sermon', 'Sermon (General)'

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    resource_type = models.CharField(
        max_length=20,
        choices=ResourceType.choices,
        default=ResourceType.SERMON,
    )
    youtube_url = models.URLField(blank=True)
    external_url = models.URLField(blank=True, help_text='Link to video/audio hosted elsewhere')
    file = models.FileField(upload_to='resources/', blank=True, null=True)
    thumbnail = models.ImageField(
        upload_to='resources/thumbs/',
        blank=True,
        null=True,
        help_text='Optional custom cover. Leave empty to use the YouTube thumbnail when a URL is set.',
    )
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    category = models.ForeignKey(
        'QuestionCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resources',
        help_text='Spiritual topic — same list as Q&A categories (e.g. Bible & Doctrine).',
    )
    published_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resources_created',
    )

    class Meta:
        ordering = ['-published_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or 'resource'
            slug = base
            counter = 1
            while Resource.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def watch_url(self):
        from .utils import youtube_watch_url

        if self.youtube_url:
            return youtube_watch_url(self.youtube_url)
        return self.external_url or ''

    @property
    def youtube_id(self):
        from .utils import youtube_video_id

        return youtube_video_id(self.youtube_url) or ''

    @property
    def has_thumbnail(self):
        return bool(self.thumbnail)

    @property
    def display_thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        if self.youtube_id:
            from .utils import youtube_thumbnail_urls

            return youtube_thumbnail_urls(self.youtube_id).get('maxres', '')
        return ''

    @property
    def display_thumbnail_fallback_url(self):
        if self.thumbnail or not self.youtube_id:
            return ''
        from .utils import youtube_thumbnail_urls

        return youtube_thumbnail_urls(self.youtube_id).get('hq', '')

    @property
    def uses_youtube_cdn_thumbnail(self):
        return bool(self.youtube_id) and not self.thumbnail

    @property
    def has_display_thumbnail(self):
        return bool(self.display_thumbnail_url)

    @property
    def primary_url(self):
        if self.file:
            return self.file.url
        if self.external_url:
            return self.external_url
        if self.youtube_url:
            return self.youtube_url
        return ''

    @property
    def has_download(self):
        return bool(self.file)

    @property
    def file_extension(self):
        if not self.file:
            return ''
        name = self.file.name.rsplit('.', 1)
        return name[-1].upper() if len(name) > 1 else 'FILE'


class Article(TimeStampedModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField()
    cover_image = models.ImageField(upload_to='articles/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
    )

    class Meta:
        ordering = ['-published_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or 'article'
            slug = base
            counter = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Book(TimeStampedModel):
    title = models.CharField(max_length=255)
    author_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='books/', blank=True, null=True)
    purchase_url = models.URLField(blank=True)
    file = models.FileField(upload_to='books/', blank=True, null=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class QuestionCategory(models.Model):
    """Site-wide spiritual topics for Q&A, videos, audio, PDFs, and sermons."""

    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        default='bi-heart',
        help_text='Bootstrap Icons class, e.g. bi-heart',
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'topic'
        verbose_name_plural = 'topics'

    def __str__(self):
        return self.name


class Question(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ANSWERED = 'answered', 'Answered'
        ARCHIVED = 'archived', 'Archived'

    asker_name = models.CharField(max_length=120)
    asker_email = models.EmailField()
    category = models.ForeignKey(
        QuestionCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
    )
    subject = models.CharField(max_length=255, blank=True)
    question_text = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    answer_text = models.TextField(
        blank=True,
        help_text='Written answer from the pastor.',
    )
    answer_youtube_url = models.URLField(
        blank=True,
        help_text='Optional YouTube video answer (full watch or youtu.be link).',
    )
    answer_youtube_thumbnail = models.ImageField(
        upload_to='qa/answer_thumbs/',
        blank=True,
        null=True,
        help_text='Optional custom cover. Leave empty to use the YouTube video thumbnail.',
    )
    recommended_resources = models.ManyToManyField(
        'Resource',
        blank=True,
        related_name='recommended_in_answers',
        help_text='Published resources to recommend alongside the answer.',
    )
    is_public = models.BooleanField(
        default=False,
        help_text='Show question and answer on the public Q&A page when answered.',
    )
    is_featured = models.BooleanField(
        default=False,
        help_text='Highlight in “Top questions” on the public Q&A page (manage up to ~20).',
    )
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions_answered',
    )
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.asker_name}: {self.subject or self.question_text[:50]}'

    @property
    def display_title(self):
        if self.subject:
            return self.subject
        text = (self.question_text or '').strip()
        if len(text) > 120:
            return text[:117] + '…'
        return text or 'Question'

    @property
    def has_answer_content(self):
        if self.answer_text and self.answer_text.strip():
            return True
        if self.answer_youtube_url:
            return True
        if self.pk and self.recommended_resources.exists():
            return True
        return False

    @property
    def answer_watch_url(self):
        from .utils import youtube_watch_url

        return youtube_watch_url(self.answer_youtube_url)

    @property
    def answer_youtube_embed(self):
        from .utils import youtube_embed_url

        return youtube_embed_url(self.answer_youtube_url)

    @property
    def answer_youtube_embed_autoplay(self):
        from .utils import youtube_embed_url

        return youtube_embed_url(self.answer_youtube_url, autoplay=True)

    @property
    def has_text_answer(self):
        return bool(self.answer_text and self.answer_text.strip())

    @property
    def has_video_answer(self):
        return bool(self.answer_youtube_url)

    @property
    def answer_youtube_id(self):
        from .utils import youtube_video_id

        return youtube_video_id(self.answer_youtube_url) or ''

    @property
    def display_answer_thumbnail_url(self):
        if self.answer_youtube_thumbnail:
            return self.answer_youtube_thumbnail.url
        if self.answer_youtube_id:
            from .utils import youtube_thumbnail_urls

            urls = youtube_thumbnail_urls(self.answer_youtube_id)
            return urls.get('hq', '') or urls.get('maxres', '')
        return ''

    @property
    def display_answer_thumbnail_fallback_url(self):
        if self.answer_youtube_thumbnail or not self.answer_youtube_id:
            return ''
        from .utils import youtube_thumbnail_urls

        urls = youtube_thumbnail_urls(self.answer_youtube_id)
        return urls.get('maxres', '') or urls.get('mq', '')

    @property
    def uses_youtube_cdn_answer_thumbnail(self):
        return bool(self.answer_youtube_id) and not self.answer_youtube_thumbnail

    @property
    def has_display_answer_thumbnail(self):
        return bool(self.display_answer_thumbnail_url)

    @property
    def has_answer_video_thumbnail(self):
        return self.has_display_answer_thumbnail

    @property
    def has_resource_answer(self):
        if not self.pk:
            return False
        return self.recommended_resources.exists()

    @property
    def status_badge_class(self):
        return {
            'pending': 'warning',
            'answered': 'success',
            'archived': 'secondary',
        }.get(self.status, 'secondary')


class ContactMessage(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        READ = 'read', 'Read'
        REPLIED = 'replied', 'Replied'
        ARCHIVED = 'archived', 'Archived'

    full_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    whatsapp_phone = models.CharField(max_length=30)
    message = models.TextField(
        help_text='Message from the visitor.',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'contact message'
        verbose_name_plural = 'contact messages'

    def __str__(self):
        return f'{self.full_name} — {self.whatsapp_phone}'

    @property
    def pastor_notify_url(self):
        """Link to send the submission to the pastor's WhatsApp (0783558316)."""
        from .utils import contact_inbound_message, pastor_whatsapp_link
        return pastor_whatsapp_link(contact_inbound_message(self))

    @property
    def reply_whatsapp_url(self):
        """Link for the pastor to reply to the visitor on their WhatsApp number."""
        from .utils import reply_to_visitor_whatsapp_link
        return reply_to_visitor_whatsapp_link(self)

    @property
    def reply_email_url(self):
        from .utils import contact_reply_email_url
        return contact_reply_email_url(self)

    @property
    def status_badge_class(self):
        return {
            'pending': 'warning',
            'read': 'secondary',
            'replied': 'success',
            'archived': 'dark',
        }.get(self.status, 'secondary')


class DashboardNotification(TimeStampedModel):
    class NotificationType(models.TextChoices):
        CONTACT = 'contact', 'Get in Touch'
        QUESTION = 'question', 'New Question'
        SYSTEM = 'system', 'System'

    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    related_contact = models.ForeignKey(
        ContactMessage,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
    )
    related_question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def display_name(self):
        if self.related_contact_id:
            return self.related_contact.full_name
        if self.related_question_id:
            return self.related_question.asker_name
        return self.title.split(':', 1)[-1].strip()

    @property
    def display_phone(self):
        if self.related_contact_id:
            return self.related_contact.whatsapp_phone
        phone = self._extract_from_message('WhatsApp:', 'Email:')
        if phone:
            return phone
        return self._extract_from_message('Phone:', 'Email:')

    @property
    def display_email(self):
        if self.related_contact_id and self.related_contact.email:
            return self.related_contact.email
        if self.related_question_id:
            return self.related_question.asker_email
        return self._extract_from_message('Email:', 'Message:')

    @property
    def display_message_preview(self):
        if self.related_contact_id and self.related_contact.message:
            return self.related_contact.message
        if self.related_question_id:
            return self.related_question.question_text
        return self.message

    @property
    def type_badge_class(self):
        mapping = {
            'contact': 'contact',
            'question': 'question',
            'system': 'system',
            'appointment': 'legacy',
        }
        return mapping.get(self.notification_type, 'system')

    def get_dashboard_url(self):
        """Resolve admin link from related question/contact when possible."""
        from django.urls import reverse

        if self.related_question_id:
            return reverse('dashboard_answer_question', args=[self.related_question_id])
        if self.related_contact_id:
            return reverse('dashboard_message_detail', args=[self.related_contact_id])
        if self.link and self.link.startswith('/'):
            return self.link
        return reverse('dashboard_messages')

    def _extract_from_message(self, start_label: str, end_label: str | None = None) -> str:
        text = self.message or ''
        if start_label not in text:
            return ''
        part = text.split(start_label, 1)[1]
        if end_label and end_label in part:
            part = part.split(end_label, 1)[0]
        return part.strip().split('\n')[0].strip()
