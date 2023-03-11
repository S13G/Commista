from django.db import models
from uuid import uuid4

# Create your models here.


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
