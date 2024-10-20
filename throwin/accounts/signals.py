from accounts.choices import UserKind


def post_save_user(sender, instance, created, **kwargs):
    from accounts.models import UserProfile

    if created and instance.kind == UserKind.RESTAURANT_STUFF:
        # create default profile for restaurant stuff when a new user is created
        UserProfile.objects.create(
            user=instance,
            introduction="I'm restaurant stuff.",
            total_score=0
        )
