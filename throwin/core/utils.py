"""Utils functions for core app"""

import re


def get_user_media_file_prefix(instance, filename):
    """Return the file path prefix for a user's media file."""
    return f"users/profile_pictures/{instance.uid}/{filename}"


def get_store_banner_file_prefix(instance, filename):
    """Return the file path prefix for a store's banner file."""
    return f"stores/banners/{instance.uid}_{filename}"


def get_store_logo_file_prefix(instance, filename):
    """Return the file path prefix for a store's logo file."""
    return f"stores/logos/{instance.uid}_{filename}"


def get_restaurant_banner_file_prefix(instance, filename):
    """Return the file path prefix for a store's banner file."""
    return f"restaurants/banners/{instance.uid}_{filename}"


def get_restaurant_logo_file_prefix(instance, filename):
    """Return the file path prefix for a store's logo file."""
    return f"restaurants/logos/{instance.uid}_{filename}"


def is_valid_japanese_phone_number(phone_number: str):
    # Regular expression for Japanese mobile numbers
    # Supports optional +81 for country code
    pattern = re.compile(r"^(\+81|0)(70|80|90)-\d{4}-\d{4}$")

    # Check if the phone number matches the pattern
    return bool(pattern.match(phone_number))


from decimal import Decimal
from django.core.exceptions import ValidationError


def to_decimal(value):
    """
    Safely converts a string value to a Decimal.

    Args:
        value (str): The string value to convert

    Returns:
        Decimal: The converted decimal value

    Raises:
        ValidationError: If conversion fails
    """
    try:
        # Remove any commas used as a thousand separators
        value = value.replace(',', '')
        # Handle different decimal separators
        if '.' not in value and ',' in value:
            value = value.replace(',', '.')
        return Decimal(value.strip())
    except (ValueError, TypeError):
        raise ValidationError(
            "Invalid numeric format. Please use numbers only."
        )
