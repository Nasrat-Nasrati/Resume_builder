import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [("accounts", "0003_user_pending_email")]
    operations = [migrations.CreateModel(name="CareerProfile", fields=[
        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ("professional_title", models.CharField(blank=True, max_length=160)),
        ("summary", models.TextField(blank=True, max_length=3000)),
        ("city", models.CharField(blank=True, max_length=120)),
        ("province", models.CharField(blank=True, max_length=120)),
        ("district", models.CharField(blank=True, max_length=120)),
        ("father_name", models.CharField(blank=True, max_length=160)),
        ("tazkira_number", models.CharField(blank=True, max_length=64)),
        ("show_father_name", models.BooleanField(default=False)),
        ("show_tazkira_number", models.BooleanField(default=False)),
        ("show_province", models.BooleanField(default=True)),
        ("show_district", models.BooleanField(default=True)),
        ("created_at", models.DateTimeField(auto_now_add=True)),
        ("updated_at", models.DateTimeField(auto_now=True)),
        ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="career_profile", to=settings.AUTH_USER_MODEL)),
    ], options={"ordering": ["-updated_at"]})]
