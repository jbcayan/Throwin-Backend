from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.choices import UserKind, AuthProvider
from accounts.management.commands.base_users import japanese_names

User = get_user_model()


class Command(BaseCommand):
    help = 'Create some restaurant owners'

    names = japanese_names

    def handle(self, *args, **options):
        # Create restaurant owner users
        owner_1, _ = User.objects.get_or_create(
            email="aaa@gmail.com",      # Previous: abc@gmail.com
            name="AAA",
            kind=UserKind.RESTAURANT_OWNER,
            is_active=True,
            is_verified=True,
            auth_provider=AuthProvider.EMAIL
        )
        owner_1.set_password("String1234")  # Previous: string1234
        owner_1.save()

        owner_2, _ = User.objects.get_or_create(
            email="bbb@gmail.com",      # Previous: cdc@gmail.com
            name="BBB",
            kind=UserKind.RESTAURANT_OWNER,
            is_active=True,
            is_verified=True,
            auth_provider=AuthProvider.EMAIL,
        )
        owner_2.set_password("String1234")    # Previous: password1234
        owner_2.save()

        owner_3, _ = User.objects.get_or_create(
            email="ccc@gmail.com",   # Previous:xyz@gmail.com
            name="CCC",
            kind=UserKind.RESTAURANT_OWNER,
            is_active=True,
            is_verified=True,
            auth_provider=AuthProvider.EMAIL,
        )
        owner_3.set_password("String1234")    # Previous: password1234
        owner_3.save()

        self.stdout.write(self.style.SUCCESS('Successfully created restaurant owners'))
