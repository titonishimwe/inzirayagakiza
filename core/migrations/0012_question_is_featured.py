from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_hero_verse_content_blocks'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='is_featured',
            field=models.BooleanField(
                default=False,
                help_text='Highlight in “Top questions” on the public Q&A page (manage up to ~20).',
            ),
        ),
    ]
