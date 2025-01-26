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
            email="abc@gmail.com",
            name="ABC",
            kind=UserKind.RESTAURANT_OWNER,
            is_active=True,
            is_verified=True,
            auth_provider=AuthProvider.EMAIL
        )
        owner_1.set_password("string1234")
        owner_1.save()

        owner_2, _ = User.objects.get_or_create(
            email="cdc@gmail.com",
            password="stringd1234",
            name="CDC",
            kind=UserKind.RESTAURANT_OWNER,
            is_active=True,
            is_verified=True,
            auth_provider=AuthProvider.EMAIL,
        )
        owner_2.set_password("password1234")
        owner_2.save()

        owner_3, _ = User.objects.get_or_create(
            email="xyz@gmail.com",
            password="string1234",
            name="XYZ",
            kind=UserKind.RESTAURANT_OWNER,
            is_active=True,
            is_verified=True,
            auth_provider=AuthProvider.EMAIL,
        )
        owner_3.set_password("password1234")
        owner_3.save()

        self.stdout.write(self.style.SUCCESS('Successfully created restaurant owners'))
