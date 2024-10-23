from django.db.models import TextChoices


class StoreUserRole(TextChoices):
    ADMIN = "admin", "Admin"
    RESTAURANT_STUFF = "restaurant_stuff", "Restaurant Stuff"
    UNDEFINED = "undefined", "Undefined"
