from django.db.models import TextChoices


class Status(TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    DELETED = "deleted", "Deleted"
    PENDING = "pending", "Pending"
