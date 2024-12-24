import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tqdm import tqdm

from accounts.choices import UserKind, AuthProvider
from accounts.management.commands.base_users import japanese_names

from store.models import Store

User = get_user_model()


class Command(BaseCommand):
    help = 'Create users with Japanese names and English emails'

    names = japanese_names

    def handle(self, *args, **options):
        stores = Store().get_all_actives()

        with tqdm(total=len(self.names), desc='Creating Users', unit='user') as pbar:
            # Create a superuser
            User.objects.create_superuser(
                email="admin@gmail.com",
                password="123456",
                name="Super Admin",
            )
            self.stdout.write(f"Created superuser: Admin\n")

            for english_name, japanese_name in self.names:
                email = f"{english_name.split()[0].lower()}@example.com"

                if not User.objects.filter(email=email).exists():
                    store = random.choice(stores)

                    user = User.objects.create_user(
                        email=email,
                        password="password1234",
                        name=japanese_name,
                        kind=UserKind.RESTAURANT_STAFF,
                        is_active=True,
                        is_verified=True,
                        auth_provider=AuthProvider.EMAIL,
                        store=store,
                    )
                    self.stdout.write(f"Created user: {english_name}\n")
                else:
                    self.stdout.write(f"User already exists: {english_name}\n")

                pbar.update(1)

        self.stdout.write(self.style.SUCCESS('Successfully created users'))
