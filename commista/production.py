# "default": {
#     "ENGINE": "django.db.backends.mysql",
#     "NAME": config("DATABASE_NAME"),
#     "HOST": config("DATABASE_HOST"),
#     "USER": config("DATABASE_USER"),
#     "PASSWORD": config("DATABASE_PASSWORD"),
# }
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
