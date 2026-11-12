from django.db import migrations

from core.site_settings import DEFAULT_QA_BANNER_SUBTITLE, DEFAULT_QA_BANNER_TITLE, ensure_all_site_blocks


def seed_qa_blocks(apps, schema_editor):
    ensure_all_site_blocks()
    ContentBlock = apps.get_model('core', 'ContentBlock')
    defaults = {
        'qa_banner_title': DEFAULT_QA_BANNER_TITLE,
        'qa_banner_subtitle': DEFAULT_QA_BANNER_SUBTITLE,
        'qa_featured_heading': 'Top questions',
        'qa_verse_text': (
            'All Scripture is God-breathed and is useful for teaching, rebuking, '
            'correcting and training in righteousness.'
        ),
        'qa_verse_reference': '2 Timothy 3:16-17',
    }
    for key, value in defaults.items():
        block, created = ContentBlock.objects.get_or_create(
            key=key,
            defaults={
                'label': key.replace('_', ' ').title(),
                'block_type': 'text',
                'value': value,
                'is_active': True,
            },
        )
        if created:
            continue
        if not (block.value or '').strip():
            block.value = value
            block.is_active = True
            block.save(update_fields=['value', 'is_active'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_question_is_featured'),
    ]

    operations = [
        migrations.RunPython(seed_qa_blocks, migrations.RunPython.noop),
    ]
