import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("profiles", "0001_initial")]
    operations = [migrations.CreateModel(name="Experience", fields=[
        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ("position", models.CharField(max_length=160)),
        ("employer", models.CharField(max_length=160)),
        ("location", models.CharField(blank=True, max_length=160)),
        ("start_date", models.DateField()),
        ("end_date", models.DateField(blank=True, null=True)),
        ("is_current", models.BooleanField(default=False)),
        ("duties", models.TextField(blank=True, max_length=6000)),
        ("sort_order", models.PositiveIntegerField(default=0)),
        ("created_at", models.DateTimeField(auto_now_add=True)),
        ("updated_at", models.DateTimeField(auto_now=True)),
        ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="experiences", to="profiles.careerprofile")),
    ], options={"ordering": ["sort_order", "-start_date"]}), migrations.AddConstraint(model_name="experience", constraint=models.CheckConstraint(condition=models.Q(end_date__isnull=True) | models.Q(end_date__gte=models.F("start_date")), name="experience_end_after_start"))]
