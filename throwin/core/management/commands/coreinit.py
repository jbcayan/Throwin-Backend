from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction


class Command(BaseCommand):
    help = 'Initialize the core setup by running loadstores and loadusers commands in sequence with atomic transactions'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self._extracted_from_handle_4(
                    'Starting to load restaurants...',
                    'load_restaurant',
                    'Successfully loaded restaurants.\n',
                )
                self._extracted_from_handle_4(
                    'Starting to load stores...',
                    'loadstores',
                    'Successfully loaded stores.\n',
                )
                self._extracted_from_handle_4(
                    'Starting to load users...',
                    'loadusers',
                    'Successfully loaded users.\n',
                )
            self.stdout.write(self.style.SUCCESS('Core initialization completed successfully.'))
        except CommandError as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))

    def _extracted_from_handle_4(self, arg0, arg1, arg2):
        self.stdout.write(self.style.NOTICE(arg0))
        call_command(arg1)
        self.stdout.write(self.style.SUCCESS(arg2))
