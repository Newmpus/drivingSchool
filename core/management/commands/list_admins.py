from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    help = 'List all admin users'

    def handle(self, *args, **kwargs):
        admins = User.objects.filter(role='admin')
        if not admins:
            self.stdout.write('No admin users found.')
            return
        self.stdout.write('Admin users:')
        for admin in admins:
            self.stdout.write(f'Username: {admin.username}, Email: {admin.email}')
