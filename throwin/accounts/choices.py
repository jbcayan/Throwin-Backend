from django.db.models import TextChoices


class GenderChoices(TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"


class UserKind(TextChoices):
    SUPER_ADMIN = "super_admin", "Super Admin"
    ADMIN = "admin", "Admin"
    RESTAURANT_STAFF = "restaurant_staff", "Restaurant Staff"
    CONSUMER = "consumer", "Consumer"
    UNDEFINED = "undefined", "Undefined"


class AuthProvider(TextChoices):
    EMAIL = "email", "Email"
    GOOGLE = "google", "Google"
    FACEBOOK = "facebook", "Facebook"
    LINE = "line", "Line"
    APPLE = "apple", "Apple"
