from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import CVArtifact, CVPhoto
from .tasks import cleanup_private_file

@receiver(post_delete, sender=CVPhoto)
@receiver(post_delete, sender=CVArtifact)
def queue_private_file_cleanup(sender, instance, **kwargs):
    storage_name = instance.file.name
    if storage_name:
        transaction.on_commit(lambda: cleanup_private_file.delay(storage_name))
