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
