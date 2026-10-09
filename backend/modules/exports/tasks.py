import hashlib
import json
import logging
import time
from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from .models import ExportJob
from .quota import release_export_reservation, settle_export
from .rendering import render_cv_pdf
from .docx_rendering import render_cv_docx

logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(OSError,), retry_backoff=True, retry_jitter=True, max_retries=5)
def render_export(self, job_id):
    started = time.monotonic()
    job = ExportJob.objects.select_related("document").get(pk=job_id)
    if job.status == ExportJob.SUCCEEDED and job.artifact:
        return job.id
    canonical = json.dumps(job.render_input, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != job.content_hash:
        job.status = ExportJob.FAILED
        job.failure_code = "render_input_integrity_error"
        job.save(update_fields=["status", "failure_code", "updated_at"])
        release_export_reservation(job)
        return job.id
    job.status = ExportJob.PROCESSING
    job.failure_code = ""
    job.save(update_fields=["status", "failure_code", "updated_at"])
    try:
        content = render_cv_docx(job.render_input) if job.format == ExportJob.DOCX else render_cv_pdf(job.render_input)
        extension = "docx" if job.format == ExportJob.DOCX else "pdf"
        job.artifact.save(f"{job.id}.{extension}", ContentFile(content), save=False)
        job.status = ExportJob.SUCCEEDED
        with transaction.atomic():
            job.save(update_fields=["artifact", "status", "updated_at"])
            if job.purpose == ExportJob.EXPORT:
                settle_export(job)
            document = job.document
            if job.purpose == ExportJob.EXPORT and document.lifecycle_state == document.DRAFT:
                document.lifecycle_state = document.EXPORTED
                document.save(update_fields=["lifecycle_state", "updated_at"])
    except ValueError:
        job.status = ExportJob.FAILED
        job.failure_code = "invalid_render_input"
        job.save(update_fields=["status", "failure_code", "updated_at"])
        release_export_reservation(job)
    except OSError:
        job.status = ExportJob.FAILED
        job.failure_code = "storage_unavailable"
        job.save(update_fields=["status", "failure_code", "updated_at"])
        if self.request.retries >= self.max_retries:
            release_export_reservation(job)
        raise
    except Exception:
        job.status = ExportJob.FAILED
        job.failure_code = "render_failed"
        job.save(update_fields=["status", "failure_code", "updated_at"])
        release_export_reservation(job)
        raise
    logger.info("export_job_complete id=%s purpose=%s status=%s elapsed_ms=%d", job.id, job.purpose, job.status, int((time.monotonic() - started) * 1000))
    return job.id

@shared_task(bind=True, autoretry_for=(OSError,), retry_backoff=True, retry_jitter=True, max_retries=5)
def cleanup_export_file(self, storage_name):
    from django.core.files.storage import default_storage
    if storage_name and default_storage.exists(storage_name):
        default_storage.delete(storage_name)
