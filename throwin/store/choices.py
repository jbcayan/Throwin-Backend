from django.db.models import TextChoices


class StoreUserRole(TextChoices):
    ADMIN = "admin", "Admin"
    RESTAURANT_STUFF = "restaurant_stuff", "Restaurant Stuff"
    UNDEFINED = "undefined", "Undefined"


class GachaTicketEnabled(TextChoices):
    YES = "yes", "Yes"
    NO = "no", "No"
    UNDEFINED = "undefined", "Undefined"


class ExposeStatus(TextChoices):
    PUBLIC = "public", "Public"
    PRIVATE = "private", "Private"
    UNDEFINED = "undefined", "Undefined"

class SubscriptionStatus(TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    UNDEFINED = "undefined", "Undefined"
