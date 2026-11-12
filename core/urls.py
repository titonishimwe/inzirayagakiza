from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # Media & resources
    path(
        'videos/',
        RedirectView.as_view(pattern_name='youtube', permanent=True),
    ),
    path('audio/', views.audio_resources, name='audio'),
    path('pdf-content/', views.resource_list, {'resource_type': 'pdf'}, name='pdf_content'),
    path('slides/', views.resource_list, {'resource_type': 'slides'}, name='slides'),
    path('sermon/', views.resource_list, {'resource_type': 'sermon'}, name='sermon'),
    path('resources/', views.resource_list, name='resources'),
    path('youtube/', views.youtube_videos, name='youtube'),
    # Q&A & contact
    path('qa/', views.qa_page, name='qa'),
    path('qa/<int:pk>/', views.qa_question_detail, name='qa_detail'),
    path('topics/<slug:slug>/', views.topic_hub, name='topic_hub'),
    path('get-in-touch/', views.get_in_touch_page, name='get_in_touch'),
    path(
        'appointment/',
        RedirectView.as_view(pattern_name='get_in_touch', permanent=True),
    ),
    path('search/', views.search, name='search'),
    # Dashboard
    path('dashboard/login/', views.dashboard_login, name='dashboard_login'),
    path('dashboard/logout/', views.dashboard_logout, name='dashboard_logout'),
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    path('dashboard/account/', views.dashboard_account, name='dashboard_account'),
    path('dashboard/resources/', views.dashboard_resources, name='dashboard_resources'),
    path(
        'dashboard/resources/add/',
        views.dashboard_resource_add,
        name='dashboard_resource_add',
    ),
    path(
        'dashboard/resources/add/<slug:resource_type>/',
        views.dashboard_resource_create,
        name='dashboard_resource_create',
    ),
    path(
        'dashboard/resources/<int:pk>/',
        views.dashboard_resource_detail,
        name='dashboard_resource_detail',
    ),
    path(
        'dashboard/resources/<int:pk>/edit/',
        views.dashboard_resource_edit,
        name='dashboard_resource_edit',
    ),
    path(
        'dashboard/resources/<int:pk>/delete/',
        views.dashboard_resource_delete,
        name='dashboard_resource_delete',
    ),
    path(
        'dashboard/resources/<int:pk>/toggle-publish/',
        views.dashboard_resource_toggle_publish,
        name='dashboard_resource_toggle_publish',
    ),
    path('dashboard/questions/', views.dashboard_questions, name='dashboard_questions'),
    path(
        'dashboard/questions/<int:pk>/answer/',
        views.dashboard_answer_question,
        name='dashboard_answer_question',
    ),
    path(
        'dashboard/messages/',
        views.dashboard_messages,
        name='dashboard_messages',
    ),
    path(
        'dashboard/messages/<int:pk>/',
        views.dashboard_message_detail,
        name='dashboard_message_detail',
    ),
    path(
        'dashboard/messages/<int:pk>/delete/',
        views.dashboard_message_delete,
        name='dashboard_message_delete',
    ),
    path(
        'dashboard/messages/mark-pending-read/',
        views.dashboard_messages_mark_pending_read,
        name='dashboard_messages_mark_pending_read',
    ),
    path(
        'dashboard/contact-messages/',
        views.dashboard_contact_messages,
        name='dashboard_contact_messages',
    ),
    path(
        'dashboard/contact-messages/<int:pk>/',
        views.dashboard_contact_detail,
        name='dashboard_contact_detail',
    ),
    path(
        'dashboard/contact-messages/<int:pk>/status/',
        views.dashboard_contact_status,
        name='dashboard_contact_status',
    ),
    path(
        'dashboard/appointments/',
        RedirectView.as_view(pattern_name='dashboard_messages', permanent=True),
    ),
    path(
        'dashboard/notifications/',
        views.dashboard_notifications,
        name='dashboard_notifications',
    ),
    path(
        'dashboard/notifications/<int:pk>/read/',
        views.dashboard_notification_read,
        name='dashboard_notification_read',
    ),
    path(
        'dashboard/notifications/mark-all-read/',
        views.dashboard_notifications_mark_all_read,
        name='dashboard_notifications_mark_all_read',
    ),
    path(
        'dashboard/homepage-youtube/',
        views.dashboard_home_youtube,
        name='dashboard_home_youtube',
    ),
    path(
        'dashboard/site-content/',
        views.dashboard_site_settings,
        name='dashboard_content_blocks',
    ),
    path(
        'dashboard/site-settings/',
        views.dashboard_site_settings,
        name='dashboard_site_settings',
    ),
    path(
        'dashboard/site-content/add/',
        views.dashboard_content_block_create,
        name='dashboard_content_block_create',
    ),
    path(
        'dashboard/site-content/<int:pk>/edit/',
        views.dashboard_content_block_edit,
        name='dashboard_content_block_edit',
    ),
    path(
        'dashboard/categories/',
        views.dashboard_categories,
        name='dashboard_categories',
    ),
    path(
        'dashboard/categories/add/',
        views.dashboard_category_create,
        name='dashboard_category_create',
    ),
    path(
        'dashboard/categories/<int:pk>/edit/',
        views.dashboard_category_edit,
        name='dashboard_category_edit',
    ),
    path(
        'dashboard/categories/<int:pk>/delete/',
        views.dashboard_category_delete,
        name='dashboard_category_delete',
    ),
    path(
        'dashboard/questions/<int:pk>/',
        views.dashboard_question_detail,
        name='dashboard_question_detail',
    ),
]
