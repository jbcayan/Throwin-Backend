import random
from django.utils.text import slugify


def generate_store_code(store_name):
    """Generate a unique store code if not provided."""

    # Local import to avoid circular import issue
    from store.models import Store

    while True:
        prefix = store_name[:3].lower()
        random_digits = ''.join(str(random.randint(0, 9)) for _ in range(6))
        generated_code = f"{prefix}{random_digits}"

        # Check if the generated code is unique
        if not Store.objects.filter(code=generated_code).exists():
            return generated_code


def generate_unique_slug(name):
    """Generate a unique slug for the restaurant."""

    # Local import to avoid circular import issue
    from store.models import Restaurant

    slug = slugify(name)
    unique_slug = slug
    num = 1
    while Restaurant.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{slug}-{num}"
        num += 1
    return unique_slug
