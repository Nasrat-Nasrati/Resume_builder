import uuid
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q, F

class Migration(migrations.Migration):
    dependencies = [("profiles", "0002_experience")]
    operations = [migrations.CreateModel(name="EducationRecord", fields=[
        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ("record_type", models.CharField(choices=[("education", "Education"), ("training", "Training")], default="education", max_length=16)),
        ("qualification", models.CharField(max_length=160)),
        ("field_of_study", models.CharField(blank=True, max_length=160)),
        ("institution", models.CharField(max_length=200)),
        ("location", models.CharField(blank=True, max_length=160)),
        ("start_date", models.DateField(blank=True, null=True)),
        ("end_date", models.DateField(blank=True, null=True)),
        ("is_current", models.BooleanField(default=False)),
        ("credential_reference", models.CharField(blank=True, max_length=160)),
        ("sort_order", models.PositiveIntegerField(default=0)),
        ("created_at", models.DateTimeField(auto_now_add=True)),
        ("updated_at", models.DateTimeField(auto_now=True)),
        ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="education_records", to="profiles.careerprofile")),
    ], options={"ordering": ["sort_order", "-end_date", "-start_date"]}), migrations.AddConstraint(model_name="educationrecord", constraint=models.CheckConstraint(condition=Q(start_date__isnull=True) | Q(end_date__isnull=True) | Q(end_date__gte=F("start_date")), name="education_end_after_start"))]
