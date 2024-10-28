import random


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
