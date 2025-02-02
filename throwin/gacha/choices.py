from django.db.models import TextChoices

class GachaKind(TextChoices):
    GOLD = "gold", "Gold"
    SILVER = "silver", "Silver"
    BRONZE = "bronze", "Bronze"