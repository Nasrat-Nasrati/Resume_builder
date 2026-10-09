from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import ExportJob
from .tasks import cleanup_export_file

@receiver(post_delete, sender=ExportJob)
def queue_export_cleanup(sender, instance, **kwargs):
    storage_name = instance.artifact.name
    if storage_name:
        transaction.on_commit(lambda: cleanup_export_file.delay(storage_name))
