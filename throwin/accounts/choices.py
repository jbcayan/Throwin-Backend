from django.db.models import TextChoices


class GenderChoices(TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"


class UserKind(TextChoices):
    ADMIN = "admin", "Admin"
    RESTAURANT_STUFF = "restaurant_stuff", "Restaurant Stuff"
    CONSUMER = "consumer", "Consumer"
    UNDEFINED = "undefined", "Undefined"


class AuthProvider(TextChoices):
    EMAIL = "email", "Email"
    GOOGLE = "google", "Google"
    FACEBOOK = "facebook", "Facebook"
    LINE = "line", "Line"
    APPLE = "apple", "Apple"
