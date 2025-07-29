from django.core.management.base import BaseCommand
from core.tasks import notify_upcoming_lessons

class Command(BaseCommand):
    help = 'Send notifications for lessons starting in 10 minutes'

    def handle(self, *args, **kwargs):
        notify_upcoming_lessons()
        self.stdout.write(self.style.SUCCESS('Successfully sent lesson notifications'))
