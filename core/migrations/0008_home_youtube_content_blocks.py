from django.db import migrations

from core.home_youtube import ensure_home_youtube_blocks, migrate_legacy_featured_youtube


def forwards(apps, schema_editor):
    ensure_home_youtube_blocks()
    migrate_legacy_featured_youtube()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_contactmessage_add_message'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
