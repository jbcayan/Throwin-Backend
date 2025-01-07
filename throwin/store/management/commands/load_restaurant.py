from django.core.management.base import BaseCommand
import random

from accounts.choices import UserKind
from store.models import Restaurant
from store.management.commands.base_store import japaness_restaurants

from django.contrib.auth import get_user_model

from tqdm import tqdm

User = get_user_model()


class Command(BaseCommand):
    help = """Create restaurants with Japanese names"""

    names = japaness_restaurants

    def handle(self, *args, **options):
        owners = User.objects.filter(kind=UserKind.RESTAURANT_OWNER)

        with tqdm(total=len(self.names), desc='Creating Restaurants', unit='restaurant') as pbar:
            for english_name, japanese_name in self.names:
                owner = random.choice(owners)

                restaurant, created = Restaurant.objects.get_or_create(
                    name=japanese_name,
                    description="私たちは世界最高の食品を提供します",
                    restaurant_owner=owner,
                )
                if created:
                    self.stdout.write(f"Created restaurant: {english_name}\n")
                else:
                    self.stdout.write(f"Restaurant already exists: {english_name}\n")
                pbar.update(1)

        self.stdout.write(self.style.SUCCESS('Successfully created restaurants'))