import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("resumes", "0005_builder_step")]
    operations = [migrations.CreateModel(name="CVPhoto", fields=[
        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ("file", models.FileField(upload_to="resumes/private/photos/")),
        ("created_at", models.DateTimeField(auto_now_add=True)),
        ("document", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="photo", to="resumes.cvdocument")),
    ])]
