from django.db.models import TextChoices


class GenderChoices(TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"


class UserKind(TextChoices):
    SUPER_ADMIN = "super_admin", "Super Admin"
    FC_ADMIN = "fc_admin", "FC Admin",
    GLOW_ADMIN = "glow_admin", "Glow Admin",
    SALES_AGENT = "sales_agent", "Sales Agent",
    RESTAURANT_STAFF = "restaurant_staff", "Restaurant Staff"
    RESTAURANT_OWNER = "restaurant_owner", "Restaurant Owner",
    CONSUMER = "consumer", "Consumer"
    UNDEFINED = "undefined", "Undefined"


class AuthProvider(TextChoices):
    EMAIL = "email", "Email"
    GOOGLE = "google", "Google"
    FACEBOOK = "facebook", "Facebook"
    LINE = "line", "Line"
    APPLE = "apple", "Apple"


class PublicStatus(TextChoices):
    PUBLIC = "public", "Public"
    PRIVATE = "private", "Private"
    UNDEFINED = "undefined", "Undefined"
