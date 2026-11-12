from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_qa_page_content_blocks'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='category',
            field=models.ForeignKey(
                blank=True,
                help_text='Spiritual topic — same list as Q&A categories (e.g. Bible & Doctrine).',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='resources',
                to='core.questioncategory',
            ),
        ),
        migrations.AlterModelOptions(
            name='questioncategory',
            options={
                'ordering': ['sort_order', 'name'],
                'verbose_name': 'topic',
                'verbose_name_plural': 'topics',
            },
        ),
    ]
