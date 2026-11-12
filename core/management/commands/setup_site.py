from django.contrib.auth import get_user_model

from django.contrib.auth.models import Group

from django.core.management.base import BaseCommand



from core.site_settings import ensure_all_site_blocks



User = get_user_model()





class Command(BaseCommand):

    help = 'Create Pastor group, default content blocks, and optional superuser hints.'



    def add_arguments(self, parser):

        parser.add_argument(

            '--create-pastor',

            type=str,

            help='Username of existing user to add to Pastor group',

        )



    def handle(self, *args, **options):

        pastor_group, _ = Group.objects.get_or_create(name='Pastor')

        self.stdout.write(self.style.SUCCESS(f'Group ready: {pastor_group.name}'))



        ensure_all_site_blocks()

        self.stdout.write(self.style.SUCCESS('Default site settings blocks ensured.'))



        username = options.get('create_pastor')

        if username:

            try:

                user = User.objects.get(username=username)

                user.groups.add(pastor_group)

                self.stdout.write(

                    self.style.SUCCESS(f'Added {username} to Pastor group.')

                )

            except User.DoesNotExist:

                self.stdout.write(

                    self.style.ERROR(f'User "{username}" not found.')

                )



        self.stdout.write('Run: python manage.py populate_categories')

        self.stdout.write(

            'Next: python manage.py createsuperuser  (admin + Django admin)'

        )

        self.stdout.write(

            'Then: python manage.py setup_site --create-pastor <username>'

        )

