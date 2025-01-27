import random


def generate_store_code(store_name):
    """Generate a unique store code if not provided."""

    # Local import to avoid circular import issue
    from store.models import Store

    while True:
        generated_code = ''.join(str(random.randint(0, 9)) for _ in range(8))

        # Check if the generated code is unique
        if not Store.objects.filter(code=generated_code).exists():
            return generated_code


def generate_unique_slug(name):
    """Generate a unique slug for the restaurant."""

    # Local import to avoid circular import issue
    from store.models import Restaurant

    prefix = name.lower().replace(" ", "-")
    slug = prefix

    counter = 1
    while Restaurant.objects.filter(slug=slug).exists():
        slug = f"{prefix}-{counter}"
        counter += 1

    return slug
