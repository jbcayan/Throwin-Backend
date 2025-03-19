from accounts.choices import UserKind


def post_save_user(sender, instance, created, **kwargs):
    from accounts.models import UserProfile

    # If the user is created and a profile doesn't exist, create it
    if created:
        # Default profile data based on user kind
        default_profiles = {
            UserKind.RESTAURANT_STAFF: {"introduction": "I'm restaurant staff.", "address": "", "total_score": 0},
            UserKind.CONSUMER: {"introduction": "", "address": "", "total_score": 0},
            UserKind.RESTAURANT_OWNER: {"introduction": "I'm admin of this restaurant", "address": "",
                                        "total_score": 0},
            UserKind.FC_ADMIN: {"introduction": "I'm food court admin", "address": "", "total_score": 0},
            UserKind.SALES_AGENT: {"introduction": "I'm sales agent", "address": "", "total_score": 0},
            UserKind.SUPER_ADMIN: {"introduction": "I'm super admin", "address": "", "total_score": 0},
        }

        # Create profile if kind has a default profile defined
        if instance.kind in default_profiles:
            profile_data = default_profiles[instance.kind]
            UserProfile.objects.get_or_create(user=instance, defaults=profile_data)





from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from accounts.choices import UserKind

@receiver(post_save)
def create_user_balance(sender, instance, created, **kwargs):
    """
    Create a Balance object for a newly created User instance if the user is not a CONSUMER.
    """
    # Import User inside the function to avoid circular import issues
    from accounts.models import User
    # Ensure that this signal only runs for the User model.
    if sender != User:
        return

    if created and instance.kind not in [UserKind.CONSUMER]:
        # Use lazy lookup to get the Balance model from the correct app label.
        # Replace 'payment_service' with the actual app label if different.
        Balance = apps.get_model('payment_service', 'Balance')
        Balance.objects.get_or_create(user=instance)

