import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tqdm import tqdm

from store.management.commands.base_store import japanese_stores
from store.models import Store, Restaurant

User = get_user_model()


class Command(BaseCommand):
    help = """Create stores with Japanese names"""

    names = japanese_stores

    def handle(self, *args, **options):
        restaurants = Restaurant().get_all_actives()

        with tqdm(total=len(self.names), desc='Creating Stores', unit='store') as pbar:
            for english_name, japanese_name in self.names:
                restaurant = random.choice(restaurants)

                store, created = Store.objects.get_or_create(
                    name=japanese_name,
                    description="私たちは世界最高の食品を提供します",
                    restaurant=restaurant,
                    throwin_amounts="1000,2000,5000,10000",
                )
                if created:
                    self.stdout.write(f"Created store: {english_name}\n")
                else:
                    self.stdout.write(f"Store already exists: {english_name}\n")
                pbar.update(1)

        self.stdout.write(self.style.SUCCESS('Successfully created stores'))
