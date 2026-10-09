from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from modules.billing.services import effective_entitlement
from modules.resumes.models import ExportCharge
from .models import ExportJob, ExportReservation

RESERVATION_TTL = timedelta(hours=1)

def reclaim_abandoned(owner, now=None):
    now = now or timezone.now()
    return ExportReservation.objects.filter(owner=owner, status=ExportReservation.RESERVED, expires_at__lte=now).update(status=ExportReservation.RELEASED)

def usage_for(owner, now=None):
    now = now or timezone.now()
    reclaim_abandoned(owner, now)
    resolved = effective_entitlement(owner)
    plan = resolved["plan"]
    charges = ExportCharge.objects.filter(owner=owner, expires_at__gt=now)
    charged_ids = set(charges.values_list("document_identity", flat=True))
    reservations = ExportReservation.objects.filter(owner=owner, status=ExportReservation.RESERVED, expires_at__gt=now).exclude(document_identity__in=charged_ids)
    reserved_ids = set(reservations.values_list("document_identity", flat=True))
    used = len(charged_ids)
    reserved = len(reserved_ids)
    available = max(0, plan.export_limit - used - reserved)
    next_available_at = None
    if available == 0:
        deadlines = list(charges.values_list("expires_at", flat=True)) + list(reservations.values_list("expires_at", flat=True))
        next_available_at = min(deadlines) if deadlines else None
    return {"plan": plan, "subscription": resolved["subscription"], "used": used,
        "reserved": reserved, "available": available, "next_available_at": next_available_at}

def reserve_export(owner, job, plan):
    now = timezone.now()
    reclaim_abandoned(owner, now)
    if ExportCharge.objects.filter(owner=owner, document_identity=job.document_id).exists():
        return None
    existing = ExportReservation.objects.filter(owner=owner, document_identity=job.document_id, status=ExportReservation.RESERVED, expires_at__gt=now).first()
    if existing:
        return existing
    usage = usage_for(owner, now)
    if usage["available"] <= 0:
        return False
    return ExportReservation.objects.create(owner=owner, document_identity=job.document_id,
        job=job, status=ExportReservation.RESERVED, expires_at=now + RESERVATION_TTL)

@transaction.atomic
def settle_export(job):
    if job.purpose != ExportJob.EXPORT:
        return None
    reservation = ExportReservation.objects.select_for_update().filter(owner=job.owner,
        document_identity=job.document_id, status=ExportReservation.RESERVED).first()
    if reservation:
        plan = effective_entitlement(job.owner)["plan"]
        now = timezone.now()
        ExportCharge.objects.get_or_create(owner=job.owner, document_identity=job.document_id,
            defaults={"expires_at": now + timedelta(hours=plan.rolling_window_hours)})
        reservation.status = ExportReservation.SETTLED
        reservation.save(update_fields=["status"])
        return reservation
    return None

@transaction.atomic
def release_export_reservation(job):
    reservation = ExportReservation.objects.select_for_update().filter(owner=job.owner,
        document_identity=job.document_id, status=ExportReservation.RESERVED).first()
    if not reservation:
        return False
    still_running = ExportJob.objects.filter(owner=job.owner, document_id=job.document_id,
        purpose=ExportJob.EXPORT, status__in=[ExportJob.PENDING, ExportJob.PROCESSING]).exclude(pk=job.pk).exists()
    if still_running:
        return False
    reservation.status = ExportReservation.RELEASED
    reservation.save(update_fields=["status"])
    return True
