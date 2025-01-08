from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction


class Command(BaseCommand):
    help = 'Initialize the core setup by running commands in sequence with atomic transactions'

    def handle(self, *args, **options):
        # List of commands to execute in sequence
        commands = [
            ('Starting to load restaurant owners...', 'load_restaurant_owner', 'Successfully loaded restaurant owners.'),
            ('Starting to load restaurants...', 'load_restaurant', 'Successfully loaded restaurants.'),
            ('Starting to load stores...', 'loadstores', 'Successfully loaded stores.'),
            ('Starting to load users...', 'loadusers', 'Successfully loaded users.'),
        ]

        try:
            with transaction.atomic():
                for start_msg, command_name, success_msg in commands:
                    self._run_command_with_feedback(start_msg, command_name, success_msg)
            self.stdout.write(self.style.SUCCESS('Core initialization completed successfully.'))
        except CommandError as e:
            self.stderr.write(self.style.ERROR(f'CommandError occurred: {e}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Unexpected error: {e}'))

    def _run_command_with_feedback(self, start_message, command_name, success_message):
        """
        Helper method to run a command with feedback messages.
        """
        self.stdout.write(self.style.NOTICE(start_message))
        try:
            call_command(command_name)
            self.stdout.write(self.style.SUCCESS(success_message))
        except CommandError as e:
            raise CommandError(f'Error while executing "{command_name}": {e}')
