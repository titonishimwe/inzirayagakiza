from django.db import migrations

from core.youtube_page import ensure_youtube_page_blocks


def forwards(apps, schema_editor):
    ensure_youtube_page_blocks()
    ContentBlock = apps.get_model('core', 'ContentBlock')
    defaults = {
        'youtube_featured_video_url': 'https://youtu.be/RXrvatSzY8I',
        'youtube_featured_video_title': 'The Power of the Cross',
        'youtube_featured_video_description': (
            'Why the cross is the center of the Christian message.'
        ),
    }
    for key, value in defaults.items():
        ContentBlock.objects.filter(key=key).update(value=value)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_home_youtube_content_blocks'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
