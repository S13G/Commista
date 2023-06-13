from django.core.exceptions import ValidationError


def validate_image_size(image):
    max_size = 5 * 1024 * 1024  # 3MB in bytes
    if image.size is None:
        raise ValidationError("Please insert an image")
    elif image.size > max_size:
        raise ValidationError(f"Image size should be less than 5MB")
