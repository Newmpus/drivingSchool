from django.core.management.base import BaseCommand, CommandError
from core.models import User

class Command(BaseCommand):
    help = 'Create a new admin user with specified username and password'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the new admin user')
        parser.add_argument('password', type=str, help='Password for the new admin user')
        parser.add_argument('--email', type=str, default='', help='Email address for the new admin user')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        password = kwargs['password']
        email = kwargs['email']

        if User.objects.filter(username=username).exists():
            raise CommandError(f'User with username "{username}" already exists.')

        admin_user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            role='admin',
            is_staff=True,
            is_superuser=True,
            is_active=True,
            is_approved=True
        )
        admin_user.save()
        self.stdout.write(self.style.SUCCESS(f'Admin user "{username}" created successfully.'))
