from django.core.management.base import BaseCommand, CommandError
from core.models import User

class Command(BaseCommand):
    help = 'Reset password for an admin user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the admin user')
        parser.add_argument('password', type=str, help='New password')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        password = kwargs['password']
        try:
            admin = User.objects.get(username=username, role='admin')
        except User.DoesNotExist:
            raise CommandError(f'Admin user with username "{username}" does not exist.')

        admin.set_password(password)
        admin.save()
        self.stdout.write(self.style.SUCCESS(f'Password for admin user "{username}" has been reset successfully.'))
