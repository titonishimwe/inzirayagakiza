from django.db import migrations

from core.site_settings import ensure_all_site_blocks


def forwards(apps, schema_editor):
    ensure_all_site_blocks()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_youtube_page_featured_blocks'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
