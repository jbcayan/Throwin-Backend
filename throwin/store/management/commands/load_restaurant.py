from django.core.management.base import BaseCommand
import random

from accounts.choices import UserKind, AuthProvider
from store.models import Restaurant, RestaurantUser
from store.management.commands.base_store import japaness_restaurants

from django.contrib.auth import get_user_model

from tqdm import tqdm

User = get_user_model()


class Command(BaseCommand):
    help = """Create restaurants with Japanese names"""

    names = japaness_restaurants

    def handle(self, *args, **options):
        owners = User.objects.filter(kind=UserKind.RESTAURANT_OWNER)

        sales_agent, _ = User.objects.get_or_create(
            email="sales_agent@gmail.com",
            password="password1234",
            name="Sales Agent",
            kind=UserKind.SALES_AGENT,
            is_active=True,
            is_verified=True,
            auth_provider=AuthProvider.EMAIL,
        )
        sales_agent.set_password("password1234")
        sales_agent.save()

        with tqdm(total=len(self.names), desc='Creating Restaurants', unit='restaurant') as pbar:
            available_owners = list(owners)

            for english_name, japanese_name in self.names:
                if not available_owners:
                    self.stdout.write(self.style.WARNING("No more available owners for new restaurants. Skipping..."))
                    break  # Stop the loop when all owners are assigned

                owner = available_owners.pop(0)

                restaurant, created = Restaurant.objects.get_or_create(
                    name=japanese_name,
                    description="私たちは世界最高の食品を提供します",
                    restaurant_owner=owner,
                    sales_agent=sales_agent,
                )

                if created:
                    self.stdout.write(f"Created restaurant: {english_name}\n")

                    # Add the owner as a restaurant user
                    restaurant_user, _ = RestaurantUser.objects.get_or_create(
                        restaurant=restaurant,
                        user=owner,
                        role=UserKind.RESTAURANT_OWNER
                    )

                    self.stdout.write(f"Added owner to restaurant: {english_name}\n")

                    restaurant_user_sales, _ = RestaurantUser.objects.get_or_create(
                        restaurant=restaurant,
                        user=sales_agent,
                        role=UserKind.SALES_AGENT
                    )
                    self.stdout.write(f"Added sales agent to restaurant: {english_name}\n")

                else:
                    self.stdout.write(f"Restaurant already exists: {english_name}\n")
                pbar.update(1)

        self.stdout.write(self.style.SUCCESS('Successfully created restaurants'))