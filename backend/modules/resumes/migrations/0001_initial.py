import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [("profiles", "0005_optional_profile_entries"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name="ResumeDocument", fields=[
        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ("title", models.CharField(default="Untitled CV", max_length=160)),
        ("output_language", models.CharField(choices=[("en", "English"), ("fa", "Dari"), ("ps", "Pashto")], default="en", max_length=2)),
        ("schema_version", models.PositiveSmallIntegerField(default=1)), ("selected_sections", models.JSONField(default=list)),
        ("snapshot", models.JSONField(default=dict)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
        ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resume_documents", to=settings.AUTH_USER_MODEL)),
    ], options={"ordering": ["-updated_at"]})]
