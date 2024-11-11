from accounts.choices import UserKind

from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def post_save_user(sender, instance, created, **kwargs):
    from accounts.models import UserProfile

    default_profiles = {
        UserKind.RESTAURANT_STUFF: {"introduction": "I'm restaurant stuff.", "address": "", "total_score": 0},
        UserKind.CONSUMER: {"introduction": "", "address": "", "total_score": 0},
        UserKind.ADMIN: {"introduction": "I'm admin of this restaurant", "address": "", "total_score": 0},
        UserKind.SUPER_ADMIN: {"introduction": "I'm super admin", "address": "", "total_score": 0},
    }

    if not instance.username:
        byte_code = urlsafe_base64_encode(force_bytes(instance.id))
        instance.username = byte_code

    if created and instance.kind in default_profiles:
        profile_data = default_profiles[instance.kind]
        UserProfile.objects.create(user=instance, **profile_data)


