from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    ContactMessage,
    ContentBlock,
    DashboardNotification,
    PastorProfile,
    Question,
    QuestionCategory,
    Resource,
)


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ('key', 'label', 'block_type', 'is_active', 'updated_at')
    list_filter = ('block_type', 'is_active')
    search_fields = ('key', 'label', 'value')
    prepopulated_fields = {'key': ('label',)}


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'resource_type',
        'category',
        'is_published',
        'is_featured',
        'created_by',
        'published_at',
    )
    list_filter = ('resource_type', 'category', 'is_published', 'is_featured')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_preview')
    date_hierarchy = 'published_at'

    @admin.display(description='Thumbnail preview')
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" alt="" style="max-height:120px;border-radius:8px;">',
                obj.thumbnail.url,
            )
        return '—'

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('asker_name', 'subject', 'category', 'status', 'is_public', 'created_at')
    list_filter = ('status', 'is_public', 'category')
    search_fields = (
        'asker_name',
        'asker_email',
        'question_text',
        'answer_text',
        'answer_youtube_url',
    )
    filter_horizontal = ('recommended_resources',)
    readonly_fields = ('answered_at', 'answered_by', 'created_at', 'updated_at')
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'asker_name',
                    'asker_email',
                    'category',
                    'subject',
                    'question_text',
                    'status',
                    'is_public',
                ),
            },
        ),
        (
            'Answer',
            {
                'fields': (
                    'answer_text',
                    'answer_youtube_url',
                    'answer_youtube_thumbnail',
                    'recommended_resources',
                    'answered_by',
                    'answered_at',
                ),
            },
        ),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def save_model(self, request, obj, form, change):
        if obj.status == Question.Status.ANSWERED and obj.has_answer_content:
            if not obj.answered_by_id:
                obj.answered_by = request.user
            if not obj.answered_at:
                obj.answered_at = timezone.now()
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        if obj.status == Question.Status.ANSWERED and obj.has_answer_content:
            if not obj.answered_by_id:
                obj.answered_by = request.user
                obj.save(update_fields=['answered_by'])
            if not obj.answered_at:
                obj.answered_at = timezone.now()
                obj.save(update_fields=['answered_at'])


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'whatsapp_phone', 'email', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('full_name', 'email', 'whatsapp_phone', 'message')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DashboardNotification)
class DashboardNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PastorProfile)
class PastorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
