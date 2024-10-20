"""Utils functions for core app"""

import re


def get_user_media_file_prefix(filename):
    """Return the file path prefix for a user's media file."""
    return f"users/profile_pictures/{filename}"


def is_valid_japanese_phone_number(phone_number: str):
    # Regular expression for Japanese mobile numbers
    # Supports optional +81 for country code
    pattern = re.compile(r"^(\+81|0)(70|80|90)-\d{4}-\d{4}$")

    # Check if the phone number matches the pattern
    return bool(pattern.match(phone_number))
