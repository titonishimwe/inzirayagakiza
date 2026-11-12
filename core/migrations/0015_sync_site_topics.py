from django.db import migrations


def sync_topics(apps, schema_editor):
    QuestionCategory = apps.get_model('core', 'QuestionCategory')
    topics = [
        (
            'faith-doubt',
            'Faith & Doubt',
            'bi-question-circle',
            0,
            (
                'Belief, uncertainty, and trusting God. '
                'Use for Q&A on doubt; video/audio sermons on faith and assurance.'
            ),
        ),
        (
            'prayer-worship',
            'Prayer & Worship',
            'bi-heart',
            1,
            (
                'Prayer life, worship, and hearing from God. '
                'Use for worship teachings, prayer guides, and altar messages.'
            ),
        ),
        (
            'relationships-family',
            'Relationships & Family',
            'bi-people',
            2,
            (
                'Marriage, parenting, forgiveness, and home life. '
                'Use for family sermons and counsel-style teachings.'
            ),
        ),
        (
            'healing-restoration',
            'Healing & Restoration',
            'bi-bandaid',
            3,
            (
                'Grief, trauma, addiction recovery, and inner healing. '
                'Use for restoration testimonies and healing messages.'
            ),
        ),
        (
            'bible-doctrine',
            'Bible & Doctrine',
            'bi-book',
            4,
            (
                'Scripture, theology, and sound doctrine. '
                'Use for expository sermons, Bible studies, and teaching series.'
            ),
        ),
        (
            'anxiety-life-stress',
            'Anxiety & Life Stress',
            'bi-cloud-rain',
            5,
            (
                'Worry, depression, work pressure, and daily burdens. '
                'Use for encouragement and peace-focused messages.'
            ),
        ),
        (
            'new-believers',
            'New Believers',
            'bi-sunrise',
            6,
            (
                'First steps in Christ, baptism, church, and discipleship. '
                'Use for foundational gospel and basics-of-faith content.'
            ),
        ),
        (
            'sin-repentance',
            'Sin & Repentance',
            'bi-arrow-repeat',
            7,
            (
                'Guilt, temptation, confession, and freedom in Christ. '
                'Use for repentance, holiness, and grace-centered teaching.'
            ),
        ),
    ]
    for slug, name, icon, order, description in topics:
        QuestionCategory.objects.update_or_create(
            slug=slug,
            defaults={
                'name': name,
                'icon': icon,
                'sort_order': order,
                'description': description,
                'is_active': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_resource_category'),
    ]

    operations = [
        migrations.RunPython(sync_topics, migrations.RunPython.noop),
    ]
