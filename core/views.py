from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AnswerQuestionForm,
    ContactForm,
    ContactMessageForm,
    ContentBlockForm,
    DashboardPasswordChangeForm,
    DashboardUserProfileForm,
    DashboardUsernameForm,
    HomeYouTubeFeatureForm,
    PastorProfileForm,
    SiteSettingsForm,
    LoginForm,
    MessageFilterForm,
    QuestionCategoryForm,
    QuestionFilterForm,
    QuestionForm,
)
from .contact_filters import (
    filter_contact_messages,
    get_contact_status_counts,
    get_contact_years,
)
from .public_filters import (
    PUBLIC_GRID_PAGE_SIZE,
    QA_PAGE_SIZE,
    SEARCH_PAGE_SIZE,
    DASHBOARD_RESOURCE_PAGE_SIZE,
    filter_published_resources,
    filter_search_resources,
    get_resource_years,
    listing_filter_context,
    paginate_list,
    paginate_queryset,
)
from .question_filters import (
    filter_questions,
    get_question_category_choices,
    get_question_status_counts,
    get_question_years,
)
from .home_youtube import (
    build_home_youtube_feature,
    home_youtube_form_initial,
    migrate_legacy_featured_youtube,
    save_home_youtube_feature,
)
from .homepage_stats import get_homepage_resource_stats
from .category_helpers import (
    get_related_for_question,
    get_topic_content_summary,
    get_unified_topics_with_counts,
)
from .qa_helpers import (
    get_categories_with_counts,
    get_featured_questions,
    get_sidebar_questions,
    qa_public_queryset,
)
from .site_settings import (
    DEFAULT_HERO_VERSE_REFERENCE,
    DEFAULT_HERO_VERSE_TEXT,
    DEFAULT_QA_BANNER_SUBTITLE,
    DEFAULT_QA_BANNER_TITLE,
    ensure_all_site_blocks,
    get_public_contact,
    get_site_settings_initial,
    save_site_settings,
    sections_for_template,
)
from .youtube_page import resolve_youtube_page_featured
from .resource_forms import RESOURCE_TYPE_CONFIG, get_resource_type_slug
from .resource_pages import RESOURCE_PAGE_CONFIG
from .models import (
    ContactMessage,
    ContentBlock,
    DashboardNotification,
    PastorProfile,
    Question,
    QuestionCategory,
    Resource,
)
from .permissions import (
    can_manage_resource,
    pastor_required,
    staff_required,
    user_is_admin,
    user_is_pastor,
)
from .utils import contact_inbound_message, pastor_whatsapp_link


def get_content(key, default=''):
    try:
        block = ContentBlock.objects.get(key=key, is_active=True)
        if block.block_type == ContentBlock.BlockType.IMAGE and block.image:
            return block.image.url
        return block.value or default
    except ContentBlock.DoesNotExist:
        return default


# --- Public views ---


def home(request):
    featured = Resource.objects.filter(is_published=True, is_featured=True)[:3]
    latest_resources = Resource.objects.filter(is_published=True)[:6]
    context = {
        'hero_title': get_content('hero_title', "Inzira y'ubugingo"),
        'hero_subtitle': get_content(
            'hero_subtitle',
            'Equipping believers, spreading truth, and transforming lives through the Word of God.',
        ),
        'hero_tagline': get_content('hero_tagline', 'Teaching Gospel to the Nation'),
        'hero_verse_text': get_content('hero_verse_text', DEFAULT_HERO_VERSE_TEXT),
        'hero_verse_reference': get_content(
            'hero_verse_reference', DEFAULT_HERO_VERSE_REFERENCE
        ),
        **get_homepage_resource_stats(),
        'home_youtube': build_home_youtube_feature(),
        'featured': featured,
        'latest_resources': latest_resources,
    }
    return render(request, 'core/home.html', context)


def youtube_videos(request):
    """Public YouTube page — published videos with YouTube URL (CDN or uploaded thumbnail)."""
    from .utils import youtube_video_id
    from .youtube_page import resolve_youtube_page_featured

    get_params = request.GET.copy()
    from .category_helpers import get_topics_with_counts

    base_qs = Resource.objects.filter(
        is_published=True,
        resource_type=Resource.ResourceType.VIDEO,
    ).select_related('category')
    topics_with_counts = get_topics_with_counts(
        base_qs.exclude(youtube_url='')
    )
    qs, active_filters = filter_published_resources(
        base_qs, get_params, require_youtube=True
    )
    active_category = None
    if active_filters.get('category'):
        active_category = QuestionCategory.objects.filter(
            slug=active_filters['category'], is_active=True
        ).first()
    all_videos = list(qs)
    featured = resolve_youtube_page_featured(all_videos)
    featured_vid = youtube_video_id(featured.watch_url) if featured else None

    grid_candidates = []
    for video in all_videos:
        if featured and featured.pk and video.pk == featured.pk:
            continue
        if featured_vid and youtube_video_id(video.youtube_url) == featured_vid:
            continue
        if video.has_display_thumbnail:
            grid_candidates.append(video)

    pagination = paginate_list(grid_candidates, get_params, PUBLIC_GRID_PAGE_SIZE)

    return render(
        request,
        'core/youtube.html',
        {
            'featured_video': featured,
            'grid_videos': pagination['items'],
            'video_count': len(all_videos),
            'channel_url': get_content(
                'youtube_channel_url',
                'https://www.youtube.com/@INZIRAYUBUGINGOTV/videos',
            ),
            'active_filters': active_filters,
            'has_filters': bool(active_filters),
            'years': get_resource_years(
                Resource.objects.filter(
                    is_published=True,
                    resource_type=Resource.ResourceType.VIDEO,
                ).exclude(youtube_url='')
            ),
            'topics_with_counts': topics_with_counts,
            'active_category': active_category,
            'related_qa': (
                list(
                    _qa_base_queryset()
                    .filter(category=active_category)
                    .order_by('-answered_at')[:6]
                )
                if active_category
                else []
            ),
            **pagination,
        },
    )


def audio_resources(request):
    get_params = request.GET.copy()
    base_qs = Resource.objects.filter(
        is_published=True,
        resource_type=Resource.ResourceType.AUDIO,
    ).select_related('category')
    ctx = listing_filter_context(
        get_params,
        base_qs,
        per_page=PUBLIC_GRID_PAGE_SIZE,
        require_youtube=True,
    )
    active_category = ctx.get('active_category')
    related_qa = []
    if active_category:
        related_qa = list(
            _qa_base_queryset()
            .filter(category=active_category)
            .order_by('-answered_at')[:6]
        )
    return render(
        request,
        'core/audio.html',
        {
            'resources': ctx['items'],
            'channel_url': get_content(
                'youtube_channel_url',
                'https://www.youtube.com/@INZIRAYUBUGINGOTV/videos',
            ),
            'filter_action': request.path,
            'related_qa': related_qa,
            **ctx,
        },
    )


def resource_list(request, resource_type=None):
    get_params = request.GET.copy()
    qs = Resource.objects.filter(is_published=True)
    type_labels = {
        'video': ('Video Sermons', Resource.ResourceType.VIDEO),
        'audio': ('Audio Sermons', Resource.ResourceType.AUDIO),
        'pdf': ('PDF Resources', Resource.ResourceType.PDF),
        'slides': ('Teaching Slides', Resource.ResourceType.SLIDE),
        'sermon': ('Sermons', Resource.ResourceType.SERMON),
    }
    if resource_type and resource_type in type_labels:
        title, rtype = type_labels[resource_type]
        qs = qs.filter(resource_type=rtype)
    else:
        title = 'All Resources'

    show_manage = user_is_pastor(request.user) if request.user.is_authenticated else False
    page_config = RESOURCE_PAGE_CONFIG.get(resource_type or '')
    ctx = listing_filter_context(get_params, qs, per_page=PUBLIC_GRID_PAGE_SIZE)

    if page_config:
        return render(
            request,
            'core/resources_library.html',
            {
                'resources': ctx['items'],
                'page_config': page_config,
                'resource_type': resource_type,
                'show_manage_bar': show_manage,
                'resource_count': ctx['filtered_count'],
                'filter_action': request.path,
                **ctx,
            },
        )

    return render(
        request,
        'core/resource_list.html',
        {
            'resources': ctx['items'],
            'page_title': title,
            'resource_type': resource_type,
            'show_manage_bar': show_manage,
            'filter_action': request.path,
            **ctx,
        },
    )


def _qa_base_queryset():
    return qa_public_queryset()


def qa_page(request):
    show_ask_form = request.GET.get('ask') == '1'
    form = QuestionForm(request.POST or None)

    if request.method == 'POST':
        show_ask_form = True
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _('Thank you. Your question was received — our pastor will respond with care.'),
            )
            return redirect('qa')

    public_qa = _qa_base_queryset()

    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    answer_type = request.GET.get('type', 'all').strip()

    if query:
        public_qa = public_qa.filter(
            Q(subject__icontains=query)
            | Q(question_text__icontains=query)
            | Q(answer_text__icontains=query)
            | Q(category__name__icontains=query)
        )

    active_category = None
    if category_slug:
        active_category = QuestionCategory.objects.filter(
            slug=category_slug, is_active=True
        ).first()
        if active_category:
            public_qa = public_qa.filter(category=active_category)

    if answer_type == 'text':
        public_qa = public_qa.exclude(answer_text='')
    elif answer_type == 'video':
        public_qa = public_qa.exclude(answer_youtube_url='')
    elif answer_type == 'resources':
        public_qa = public_qa.filter(resource_count__gt=0)

    show_featured_only = request.GET.get('featured') == '1'
    if show_featured_only:
        public_qa = public_qa.filter(is_featured=True)

    categories_with_counts = get_categories_with_counts()

    get_params = request.GET.copy()
    if show_ask_form:
        get_params['ask'] = '1'
    qa_pagination = paginate_queryset(public_qa, get_params, QA_PAGE_SIZE)
    has_filters = bool(
        query or active_category or answer_type != 'all' or show_featured_only
    )
    list_pks = [q.pk for q in qa_pagination['items']]

    return render(
        request,
        'core/qa.html',
        {
            'form': form,
            'public_qa': qa_pagination['items'],
            'categories_with_counts': categories_with_counts,
            'active_category': active_category,
            'query': query,
            'answer_type': answer_type,
            'show_ask_form': show_ask_form,
            'show_featured_only': show_featured_only,
            'total_answered': _qa_base_queryset().count(),
            'featured_questions': get_featured_questions(20) if not has_filters else [],
            'sidebar_questions': get_sidebar_questions(20, exclude_pks=list_pks),
            'unified_topics': get_unified_topics_with_counts(),
            'qa_banner_title': get_content('qa_banner_title', DEFAULT_QA_BANNER_TITLE),
            'qa_banner_subtitle': get_content(
                'qa_banner_subtitle', DEFAULT_QA_BANNER_SUBTITLE
            ),
            'qa_featured_heading': get_content('qa_featured_heading', 'Top questions'),
            'qa_verse_text': get_content('qa_verse_text', DEFAULT_HERO_VERSE_TEXT),
            'qa_verse_reference': get_content(
                'qa_verse_reference', DEFAULT_HERO_VERSE_REFERENCE
            ),
            **qa_pagination,
            'has_filters': has_filters,
        },
    )


def qa_question_detail(request, pk):
    question = get_object_or_404(_qa_base_queryset(), pk=pk)
    related = get_related_for_question(question)
    return render(
        request,
        'core/qa_detail.html',
        {
            'question': question,
            'related': related,
            'sidebar_questions': get_sidebar_questions(20, exclude_pks=[pk]),
            'unified_topics': get_unified_topics_with_counts(),
            'categories_with_counts': get_categories_with_counts(),
            'active_category': question.category,
            'query': '',
            'answer_type': 'all',
            'show_featured_only': False,
            'total_answered': _qa_base_queryset().count(),
            'qa_verse_text': get_content('qa_verse_text', DEFAULT_HERO_VERSE_TEXT),
            'qa_verse_reference': get_content(
                'qa_verse_reference', DEFAULT_HERO_VERSE_REFERENCE
            ),
        },
    )


def topic_hub(request, slug):
    category = get_object_or_404(
        QuestionCategory.objects.filter(is_active=True),
        slug=slug,
    )
    content = get_topic_content_summary(category)
    return render(
        request,
        'core/topic_hub.html',
        {
            'category': category,
            'content': content,
            'unified_topics': get_unified_topics_with_counts(),
            'qa_verse_text': get_content('qa_verse_text', DEFAULT_HERO_VERSE_TEXT),
            'qa_verse_reference': get_content(
                'qa_verse_reference', DEFAULT_HERO_VERSE_REFERENCE
            ),
        },
    )


def get_in_touch_page(request):
    form = ContactForm(request.POST or None)
    whatsapp_url = None
    if request.method == 'POST' and form.is_valid():
        contact_msg = form.save()
        pastor_whatsapp = get_public_contact()['whatsapp']
        messages.success(
            request,
            _('Thank you! Your message was received. The pastor will get in touch with you soon.'),
        )
        return render(
            request,
            'core/get_in_touch.html',
            {
                'form': ContactForm(),
                'pastor_notify_url': pastor_whatsapp_link(
                    contact_inbound_message(contact_msg),
                ),
                'submitted': True,
                'pastor_whatsapp': pastor_whatsapp,
            },
        )
    return render(
        request,
        'core/get_in_touch.html',
        {'form': form, 'pastor_whatsapp': get_public_contact()['whatsapp']},
    )


def search(request):
    get_params = request.GET.copy()
    q = get_params.get('q', '').strip()
    results = []
    active_filters = {}
    pagination = {
        'page_obj': None,
        'filter_querystring': get_params.urlencode(),
        'filtered_count': 0,
    }
    if q:
        qs = Resource.objects.filter(is_published=True)
        qs, active_filters = filter_search_resources(qs, get_params)
        pagination = paginate_queryset(qs, get_params, SEARCH_PAGE_SIZE)
        results = pagination['items']
    return render(
        request,
        'core/search.html',
        {
            'query': q,
            'results': results,
            'active_filters': active_filters,
            'has_filters': bool(active_filters),
            **pagination,
        },
    )


# Legacy URL aliases
def sermon(request):
    return resource_list(request, 'sermon')


# --- Auth ---


def dashboard_login(request):
    if request.user.is_authenticated and (user_is_pastor(request.user) or user_is_admin(request.user)):
        return redirect('dashboard_home')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('dashboard_home')
    return render(request, 'core/dashboard/login.html', {'form': form})


@login_required
def dashboard_logout(request):
    logout(request)
    return redirect('home')


@pastor_required
def dashboard_account(request):
    user = request.user
    profile, _ = PastorProfile.objects.get_or_create(user=user)

    profile_form = DashboardUserProfileForm(
        request.POST or None, instance=user, prefix='profile'
    )
    username_form = DashboardUsernameForm(
        user, request.POST or None, prefix='username'
    )
    password_form = DashboardPasswordChangeForm(
        user, request.POST or None, prefix='password'
    )
    pastor_form = PastorProfileForm(
        request.POST or None, instance=profile, prefix='pastor'
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'profile' and profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated.')
            return redirect('dashboard_account')
        if action == 'username' and username_form.is_valid():
            user.username = username_form.cleaned_data['username']
            user.save(update_fields=['username'])
            messages.success(request, 'Username updated. Use it next time you sign in.')
            return redirect('dashboard_account')
        if action == 'password' and password_form.is_valid():
            user.set_password(password_form.cleaned_data['new_password1'])
            user.save(update_fields=['password'])
            from django.contrib.auth import update_session_auth_hash

            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('dashboard_account')
        if action == 'pastor' and pastor_form.is_valid():
            pastor_form.save()
            messages.success(request, 'Pastor details updated.')
            return redirect('dashboard_account')

    return render(
        request,
        'core/dashboard/account.html',
        {
            'profile_form': profile_form,
            'username_form': username_form,
            'password_form': password_form,
            'pastor_form': pastor_form,
            'is_admin': user_is_admin(user),
        },
    )


# --- Dashboard ---


@login_required
def dashboard_home(request):
    if not user_is_pastor(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    pending_questions = Question.objects.filter(status=Question.Status.PENDING).count()
    message_counts = get_contact_status_counts()
    pending_contacts = message_counts['pending']
    context = {
        'pending_questions': pending_questions,
        'pending_contacts': pending_contacts,
        'message_counts': message_counts,
        'resource_count': Resource.objects.count(),
        'answered_count': Question.objects.filter(status=Question.Status.ANSWERED).count(),
        'recent_messages': ContactMessage.objects.order_by('-created_at')[:6],
        'recent_pending': Question.objects.filter(status=Question.Status.PENDING).order_by(
            '-created_at'
        )[:4],
        'unread_question_notifications': DashboardNotification.objects.filter(
            is_read=False,
            notification_type=DashboardNotification.NotificationType.QUESTION,
        )
        .select_related('related_question')
        .order_by('-created_at')[:4],
        'is_admin': user_is_admin(request.user),
    }
    return render(request, 'core/dashboard/index.html', context)


@pastor_required
def dashboard_resources(request):
    get_params = request.GET.copy()
    resources = Resource.objects.select_related(
        'created_by', 'category'
    ).order_by('-created_at')
    active_type = get_params.get('type', '').strip()
    if active_type in RESOURCE_TYPE_CONFIG:
        db_type = RESOURCE_TYPE_CONFIG[active_type]['form'].resource_type_value
        resources = resources.filter(resource_type=db_type)

    q = get_params.get('q', '').strip()
    if q:
        resources = resources.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )

    pagination = paginate_queryset(resources, get_params, DASHBOARD_RESOURCE_PAGE_SIZE)

    type_filters = []
    for slug, cfg in RESOURCE_TYPE_CONFIG.items():
        count = Resource.objects.filter(
            resource_type=cfg['form'].resource_type_value
        ).count()
        type_filters.append({
            'slug': slug,
            'label': cfg['label'],
            'icon': cfg['icon'],
            'count': count,
        })

    return render(
        request,
        'core/dashboard/resources.html',
        {
            'resources': pagination['items'],
            'active_type': active_type if active_type in RESOURCE_TYPE_CONFIG else '',
            'type_filters': type_filters,
            'is_admin': user_is_admin(request.user),
            'search_q': q,
            **pagination,
        },
    )


def _check_resource_access(request, resource):
    if not can_manage_resource(request.user, resource):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied


@pastor_required
def dashboard_resource_add(request):
    return render(
        request,
        'core/dashboard/resource_add_hub.html',
        {'resource_types': RESOURCE_TYPE_CONFIG},
    )


def _resource_form_context(slug, form, action, resource=None):
    from .category_helpers import get_active_topics

    cfg = RESOURCE_TYPE_CONFIG[slug]
    return {
        'form': form,
        'action': action,
        'resource': resource,
        'type_slug': slug,
        'type_label': cfg['label'],
        'type_icon': cfg['icon'],
        'type_color': cfg['color'],
        'type_description': cfg['description'],
        'topics': get_active_topics(),
        'topic_required': slug in ('video', 'audio'),
    }


@pastor_required
def dashboard_resource_create(request, resource_type):
    if resource_type not in RESOURCE_TYPE_CONFIG:
        return redirect('dashboard_resource_add')

    FormClass = RESOURCE_TYPE_CONFIG[resource_type]['form']
    form = FormClass(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        resource = form.save(commit=False)
        resource.created_by = request.user
        resource.save()
        messages.success(
            request,
            f'{RESOURCE_TYPE_CONFIG[resource_type]["label"]} published successfully.',
        )
        return redirect(f"{reverse('dashboard_resources')}?type={resource_type}")

    ctx = _resource_form_context(resource_type, form, 'Add')
    return render(request, 'core/dashboard/resource_form.html', ctx)


@pastor_required
def dashboard_resource_detail(request, pk):
    resource = get_object_or_404(
        Resource.objects.select_related('created_by'),
        pk=pk,
    )
    slug = get_resource_type_slug(resource)
    cfg = RESOURCE_TYPE_CONFIG.get(slug, {})
    return render(
        request,
        'core/dashboard/resource_detail.html',
        {
            'resource': resource,
            'type_label': cfg.get('label', resource.get_resource_type_display()),
            'type_icon': cfg.get('icon', 'bi-file-earmark'),
            'can_manage': can_manage_resource(request.user, resource),
            'is_admin': user_is_admin(request.user),
        },
    )


@pastor_required
def dashboard_resource_edit(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    _check_resource_access(request, resource)

    slug = get_resource_type_slug(resource)
    FormClass = RESOURCE_TYPE_CONFIG[slug]['form']
    form = FormClass(request.POST or None, request.FILES or None, instance=resource)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Resource updated.')
        slug = get_resource_type_slug(resource)
        return redirect(f"{reverse('dashboard_resources')}?type={slug}")

    ctx = _resource_form_context(slug, form, 'Edit', resource=resource)
    ctx['can_manage'] = can_manage_resource(request.user, resource)
    return render(request, 'core/dashboard/resource_form.html', ctx)


@pastor_required
def dashboard_resource_delete(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    _check_resource_access(request, resource)
    if request.method == 'POST':
        title = resource.title
        slug = get_resource_type_slug(resource)
        resource.delete()
        messages.success(request, f'"{title}" was deleted.')
        if slug:
            return redirect(f"{reverse('dashboard_resources')}?type={slug}")
        return redirect('dashboard_resources')
    return render(
        request,
        'core/dashboard/resource_confirm_delete.html',
        {'resource': resource},
    )


@pastor_required
def dashboard_resource_toggle_publish(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    _check_resource_access(request, resource)
    if request.method == 'POST':
        resource.is_published = not resource.is_published
        resource.save(update_fields=['is_published', 'updated_at'])
        state = 'published' if resource.is_published else 'unpublished'
        messages.success(request, f'"{resource.title}" is now {state}.')
        slug = get_resource_type_slug(resource)
        return redirect(f"{reverse('dashboard_resources')}?type={slug}")
    return redirect('dashboard_resources')


@pastor_required
def dashboard_questions(request):
    get_params = request.GET.copy()
    qs, active_filters = filter_questions(get_params)
    status_counts = get_question_status_counts()
    filter_form = QuestionFilterForm(
        get_params or None,
        year_choices=get_question_years(),
        category_choices=get_question_category_choices(),
    )
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(get_params.get('page', 1))
    query_params = get_params.copy()
    query_params.pop('page', None)

    public_qa_count = Question.objects.filter(
        status=Question.Status.ANSWERED,
        is_public=True,
    ).count()
    featured_count = Question.objects.filter(
        status=Question.Status.ANSWERED,
        is_public=True,
        is_featured=True,
    ).count()

    return render(
        request,
        'core/dashboard/questions.html',
        {
            'page_obj': page_obj,
            'questions': page_obj.object_list,
            'filter_form': filter_form,
            'active_filters': active_filters,
            'status_counts': status_counts,
            'pending_count': status_counts['pending'],
            'filtered_count': paginator.count,
            'total_count': status_counts['all'],
            'public_qa_count': public_qa_count,
            'featured_count': featured_count,
            'has_filters': bool(active_filters),
            'filter_querystring': query_params.urlencode(),
        },
    )


@pastor_required
def dashboard_answer_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    form = AnswerQuestionForm(
        request.POST or None,
        request.FILES or None,
        instance=question,
    )
    if request.method == 'POST' and form.is_valid():
        q = form.save(commit=False)
        q.status = Question.Status.ANSWERED
        q.answered_by = request.user
        q.answered_at = timezone.now()
        q.save()
        form.save_m2m()
        messages.success(request, 'Answer saved.')
        return redirect('dashboard_question_detail', pk=question.pk)
    if not form.initial.get('status'):
        form.initial['status'] = Question.Status.ANSWERED
    related = get_related_for_question(question) if question.category_id else None
    return render(
        request,
        'core/dashboard/answer_question.html',
        {'form': form, 'question': question, 'related': related},
    )


def _sync_contact_notifications(contact):
    """Keep legacy notification rows in sync when linked to a contact."""
    if contact.status != ContactMessage.Status.PENDING:
        DashboardNotification.objects.filter(related_contact=contact).update(
            is_read=True,
        )


def _messages_list_context(request, get_params):
    if get_params.get('unread') == '1' and 'status' not in get_params:
        get_params['status'] = 'pending'

    qs, active_filters = filter_contact_messages(get_params)
    filter_form = MessageFilterForm(
        get_params or None,
        year_choices=get_contact_years(),
    )
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(get_params.get('page', 1))
    query_params = get_params.copy()
    query_params.pop('page', None)
    status_counts = get_contact_status_counts()

    return {
        'page_obj': page_obj,
        'inbox_messages': page_obj.object_list,
        'filter_form': filter_form,
        'active_filters': active_filters,
        'filtered_count': paginator.count,
        'total_count': status_counts['all'],
        'status_counts': status_counts,
        'pending_count': status_counts['pending'],
        'has_filters': bool(active_filters),
        'filter_querystring': query_params.urlencode(),
        'pastor_whatsapp': get_public_contact()['whatsapp'],
    }


@pastor_required
def dashboard_messages(request):
    get_params = request.GET.copy()
    return render(
        request,
        'core/dashboard/messages.html',
        _messages_list_context(request, get_params),
    )


@pastor_required
def dashboard_contact_messages(request):
    return dashboard_messages(request)


@pastor_required
def dashboard_notifications(request):
    return redirect('dashboard_messages')


@pastor_required
def dashboard_message_detail(request, pk):
    contact = get_object_or_404(ContactMessage, pk=pk)
    form = ContactMessageForm(request.POST or None, instance=contact)
    if request.method == 'POST' and form.is_valid():
        contact = form.save()
        _sync_contact_notifications(contact)
        messages.success(request, 'Message updated.')
        return redirect('dashboard_message_detail', pk=pk)
    return render(
        request,
        'core/dashboard/message_detail.html',
        {
            'contact': contact,
            'form': form,
            'pastor_whatsapp': get_public_contact()['whatsapp'],
            'status_choices': ContactMessage.Status.choices,
        },
    )


@pastor_required
def dashboard_contact_detail(request, pk):
    return dashboard_message_detail(request, pk)


@pastor_required
@require_POST
def dashboard_contact_status(request, pk):
    contact = get_object_or_404(ContactMessage, pk=pk)
    new_status = request.POST.get('status')
    if new_status in dict(ContactMessage.Status.choices):
        contact.status = new_status
        contact.save(update_fields=['status', 'updated_at'])
        _sync_contact_notifications(contact)
        messages.success(request, f'Message marked as {contact.get_status_display()}.')
    next_url = request.POST.get('next', '').strip()
    if next_url.startswith('/') and 'dashboard/messages' in next_url:
        return redirect(next_url)
    return redirect('dashboard_messages')


@pastor_required
@require_POST
def dashboard_messages_mark_pending_read(request):
    updated = ContactMessage.objects.filter(
        status=ContactMessage.Status.PENDING,
    ).update(status=ContactMessage.Status.READ)
    DashboardNotification.objects.filter(
        related_contact__status=ContactMessage.Status.READ,
        is_read=False,
    ).update(is_read=True)
    messages.success(request, f'{updated} message(s) marked as read.')
    next_url = request.POST.get('next', '').strip()
    if next_url.startswith('/') and 'dashboard/messages' in next_url:
        return redirect(next_url)
    return redirect('dashboard_messages')


@pastor_required
def dashboard_message_delete(request, pk):
    contact = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        name = contact.full_name
        contact.delete()
        messages.success(request, f'Message from "{name}" was deleted.')
        return redirect('dashboard_messages')
    return render(
        request,
        'core/dashboard/message_confirm_delete.html',
        {'contact': contact},
    )


@login_required
@require_POST
def dashboard_notification_read(request, pk):
    if not user_is_admin(request.user) and not user_is_pastor(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    notification = get_object_or_404(DashboardNotification, pk=pk)
    notification.is_read = True
    notification.save(update_fields=['is_read', 'updated_at'])
    return redirect(notification.get_dashboard_url())


@pastor_required
@require_POST
def dashboard_notifications_mark_all_read(request):
    return dashboard_messages_mark_pending_read(request)


@pastor_required
def dashboard_home_youtube(request):
    return redirect(f"{reverse('dashboard_content_blocks')}#homepage-youtube")


@pastor_required
def dashboard_site_settings(request):
    from .home_youtube import build_home_youtube_feature, migrate_legacy_featured_youtube

    migrate_legacy_featured_youtube()
    ensure_all_site_blocks()
    FormClass = SiteSettingsForm
    form = FormClass(
        request.POST or None,
        request.FILES or None,
        initial=get_site_settings_initial() if request.method != 'POST' else None,
    )
    if request.method == 'POST' and form.is_valid():
        save_site_settings(
            form.cleaned_data,
            thumbnail_file=form.cleaned_data.get('home_youtube_thumbnail'),
            remove_thumbnail=form.cleaned_data.get('remove_home_thumbnail'),
        )
        messages.success(request, 'Site settings saved successfully.')
        return redirect('dashboard_content_blocks')

    home_preview = build_home_youtube_feature()
    yt_resources = list(
        Resource.objects.filter(
            is_published=True,
            resource_type=Resource.ResourceType.VIDEO,
        ).exclude(youtube_url='').order_by('-is_featured', '-published_at'),
    )
    return render(
        request,
        'core/dashboard/site_settings.html',
        {
            'form': form,
            'sections': sections_for_template(form),
            'home_preview': home_preview,
            'youtube_page_featured': resolve_youtube_page_featured(yt_resources),
            'homepage_stats': get_homepage_resource_stats(),
        },
    )


@pastor_required
def dashboard_content_block_edit(request, pk):
    block = get_object_or_404(ContentBlock, pk=pk)
    form = ContentBlockForm(request.POST or None, request.FILES or None, instance=block)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{block.label}" updated.')
        return redirect('dashboard_content_blocks')
    return render(
        request,
        'core/dashboard/content_block_form.html',
        {'form': form, 'block': block},
    )


@pastor_required
def dashboard_content_block_create(request):
    messages.info(
        request,
        'Use Site settings to manage all site content. Advanced blocks can be edited below.',
    )
    form = ContentBlockForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        block = form.save()
        messages.success(request, f'Content block "{block.label}" created.')
        return redirect('dashboard_content_blocks')
    return render(
        request,
        'core/dashboard/content_block_form.html',
        {'form': form, 'block': None},
    )


@pastor_required
def dashboard_categories(request):
    categories = QuestionCategory.objects.annotate(
        question_count=Count('questions'),
        resource_count=Count('resources'),
    ).order_by('sort_order', 'name')
    return render(
        request,
        'core/dashboard/categories.html',
        {'categories': categories},
    )


@pastor_required
def dashboard_category_create(request):
    form = QuestionCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category created.')
        return redirect('dashboard_categories')
    return render(
        request,
        'core/dashboard/category_form.html',
        {'form': form, 'action': 'Add category'},
    )


@pastor_required
def dashboard_category_edit(request, pk):
    category = get_object_or_404(QuestionCategory, pk=pk)
    form = QuestionCategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('dashboard_categories')
    return render(
        request,
        'core/dashboard/category_form.html',
        {'form': form, 'action': 'Edit category', 'category': category},
    )


@pastor_required
def dashboard_category_delete(request, pk):
    category = get_object_or_404(QuestionCategory, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect('dashboard_categories')
    return render(
        request,
        'core/dashboard/category_confirm_delete.html',
        {'category': category},
    )


@pastor_required
def dashboard_question_detail(request, pk):
    question = get_object_or_404(
        Question.objects.select_related('category', 'answered_by').prefetch_related(
            'recommended_resources'
        ),
        pk=pk,
    )
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'archive':
            question.status = Question.Status.ARCHIVED
            question.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Question archived.')
        elif action == 'pending':
            question.status = Question.Status.PENDING
            question.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Question marked as pending.')
        elif action == 'toggle_public' and question.status == Question.Status.ANSWERED:
            question.is_public = not question.is_public
            if not question.is_public:
                question.is_featured = False
                question.save(update_fields=['is_public', 'is_featured', 'updated_at'])
            else:
                question.save(update_fields=['is_public', 'updated_at'])
            state = 'public' if question.is_public else 'private'
            messages.success(request, f'Answer is now {state}.')
        elif action == 'toggle_featured' and question.status == Question.Status.ANSWERED:
            if not question.is_public:
                messages.warning(
                    request,
                    'Publish the answer on the public Q&A page before featuring it.',
                )
            else:
                question.is_featured = not question.is_featured
                question.save(update_fields=['is_featured', 'updated_at'])
                state = 'featured' if question.is_featured else 'unfeatured'
                messages.success(request, f'Question is now {state}.')
        elif action == 'delete':
            question.delete()
            messages.success(request, 'Question deleted.')
            return redirect('dashboard_questions')
        return redirect('dashboard_question_detail', pk=pk)
    return render(
        request,
        'core/dashboard/question_detail.html',
        {'question': question},
    )
