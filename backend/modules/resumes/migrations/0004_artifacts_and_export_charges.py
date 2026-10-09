import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("resumes", "0003_archive_restore_state"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="CVArtifact", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("file", models.FileField(upload_to="resumes/private/")),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="artifacts", to="resumes.cvdocument")),
        ]),
        migrations.CreateModel(name="ExportCharge", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("document_identity", models.UUIDField()), ("charged_at", models.DateTimeField(auto_now_add=True)), ("expires_at", models.DateTimeField()),
            ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="export_charges", to=settings.AUTH_USER_MODEL)),
        ], options={"indexes": [models.Index(fields=["owner", "expires_at"], name="export_charge_owner_expiry_idx")]}),
        migrations.AddConstraint(model_name="exportcharge", constraint=models.UniqueConstraint(fields=("owner", "document_identity"), name="unique_export_charge_per_document")),
    ]
