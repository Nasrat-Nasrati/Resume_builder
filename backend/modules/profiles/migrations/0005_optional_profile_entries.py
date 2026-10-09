import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("profiles", "0004_languages_skills")]
    operations = [
        migrations.AddField(model_name="careerprofile", name="include_projects", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="careerprofile", name="include_awards", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="careerprofile", name="include_publications", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="careerprofile", name="include_references", field=models.BooleanField(default=False)),
        migrations.CreateModel(name="OptionalProfileEntry", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("entry_type", models.CharField(choices=[("project", "Project"), ("award", "Award"), ("publication", "Publication"), ("reference", "Reference")], max_length=16)),
            ("title", models.CharField(max_length=200)), ("organization", models.CharField(blank=True, max_length=200)),
            ("description", models.TextField(blank=True, max_length=5000)), ("url", models.URLField(blank=True, max_length=500)),
            ("date", models.DateField(blank=True, null=True)), ("referee_name", models.CharField(blank=True, max_length=160)),
            ("referee_role", models.CharField(blank=True, max_length=160)), ("referee_email", models.EmailField(blank=True, max_length=254)),
            ("referee_phone", models.CharField(blank=True, max_length=32)), ("consent_to_publish", models.BooleanField(default=False)),
            ("sort_order", models.PositiveIntegerField(default=0)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="optional_entries", to="profiles.careerprofile")),
        ], options={"ordering": ["sort_order", "-date", "title"]}),
    ]
