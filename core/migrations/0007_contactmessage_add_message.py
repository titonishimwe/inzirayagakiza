from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_contact_message_replace_appointment'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactmessage',
            name='message',
            field=models.TextField(
                default='',
                help_text='Message from the visitor.',
            ),
            preserve_default=False,
        ),
    ]
