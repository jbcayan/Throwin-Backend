from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction


class Command(BaseCommand):
    help = 'Initialize the core setup by running loadstores and loadusers commands in sequence with atomic transactions'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.stdout.write(self.style.NOTICE('Starting to load stores...'))
                call_command('loadstores')
                self.stdout.write(self.style.SUCCESS('Successfully loaded stores.\n'))

                self.stdout.write(self.style.NOTICE('Starting to load users...'))
                call_command('loadusers')
                self.stdout.write(self.style.SUCCESS('Successfully loaded users.\n'))

            self.stdout.write(self.style.SUCCESS('Core initialization completed successfully.'))
        except CommandError as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))
