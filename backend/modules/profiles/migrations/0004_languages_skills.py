import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("profiles", "0003_educationrecord")]
    operations = [
        migrations.CreateModel(name="LanguageEntry", fields=[("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("language", models.CharField(max_length=100)), ("is_mother_tongue", models.BooleanField(default=False)), ("proficiency", models.CharField(blank=True, choices=[("basic", "Basic"), ("conversational", "Conversational"), ("professional", "Professional"), ("fluent", "Fluent")], max_length=20)), ("cefr_level", models.CharField(blank=True, choices=[("A1", "A1"), ("A2", "A2"), ("B1", "B1"), ("B2", "B2"), ("C1", "C1"), ("C2", "C2")], max_length=2)), ("sort_order", models.PositiveIntegerField(default=0)), ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="languages", to="profiles.careerprofile"))], options={"ordering": ["sort_order", "language"]}),
        migrations.AddConstraint(model_name="languageentry", constraint=models.UniqueConstraint(fields=("profile", "language"), name="unique_profile_language")),
        migrations.CreateModel(name="SkillGroup", fields=[("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("name", models.CharField(max_length=100)), ("sort_order", models.PositiveIntegerField(default=0)), ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="skill_groups", to="profiles.careerprofile"))], options={"ordering": ["sort_order", "name"]}),
        migrations.CreateModel(name="Skill", fields=[("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("name", models.CharField(max_length=120)), ("sort_order", models.PositiveIntegerField(default=0)), ("group", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="skills", to="profiles.skillgroup"))], options={"ordering": ["sort_order", "name"]}),
        migrations.AddConstraint(model_name="skill", constraint=models.UniqueConstraint(fields=("group", "name"), name="unique_skill_in_group")),
    ]
