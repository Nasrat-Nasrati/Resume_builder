from celery import shared_task
from django.core.files.storage import default_storage

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=8)
def cleanup_private_file(self, storage_name):
    """Idempotently remove a private file left behind by a deleted document."""
    if storage_name and default_storage.exists(storage_name):
        default_storage.delete(storage_name)
    return True
