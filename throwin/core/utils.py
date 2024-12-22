"""Utils functions for core app"""

import re


def get_user_media_file_prefix(instance, filename):
    """Return the file path prefix for a user's media file."""
    return f"users/profile_pictures/{instance.uid}/{filename}"


def get_store_banner_file_prefix(instance, filename):
    """Return the file path prefix for a store's banner file."""
    return f"stores/banners/{instance.name}_{filename}"


def get_store_logo_file_prefix(instance, filename):
    """Return the file path prefix for a store's logo file."""
    return f"stores/logos/{instance.name}_{filename}"


def is_valid_japanese_phone_number(phone_number: str):
    # Regular expression for Japanese mobile numbers
    # Supports optional +81 for country code
    pattern = re.compile(r"^(\+81|0)(70|80|90)-\d{4}-\d{4}$")

    # Check if the phone number matches the pattern
    return bool(pattern.match(phone_number))
