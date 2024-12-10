import uuid

from django.db import models

from common.choices import Status


# Create your models here.
class BaseModel(models.Model):
    uid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Created Person",
        related_name="%(class)s_created_by",
    )
    updated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Updated Person",
        related_name="%(class)s_updated_by",
    )

    class Meta:
        abstract = True

    def get_all_actives(self):
        return self.__class__.objects.filter(status=Status.ACTIVE).order_by("-id")
