from django.db import migrations

from core.site_settings import (
    DEFAULT_HERO_VERSE_REFERENCE,
    DEFAULT_HERO_VERSE_TEXT,
    ensure_all_site_blocks,
)


def seed_hero_verse(apps, schema_editor):
    ContentBlock = apps.get_model('core', 'ContentBlock')
    ensure_all_site_blocks()
    defaults = {
        'hero_verse_text': DEFAULT_HERO_VERSE_TEXT,
        'hero_verse_reference': DEFAULT_HERO_VERSE_REFERENCE,
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
        ('core', '0010_site_settings_contact_social'),
    ]

    operations = [
        migrations.RunPython(seed_hero_verse, migrations.RunPython.noop),
    ]
