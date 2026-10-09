from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("resumes", "0001_initial")]
    operations = [
        migrations.RenameModel(old_name="ResumeDocument", new_name="CVDocument"),
        migrations.AddField(model_name="cvdocument", name="cv_type", field=models.CharField(choices=[("general", "General"), ("public_service", "Public service"), ("academic", "Academic"), ("scholarship", "Scholarship"), ("private_sector", "Private sector")], default="general", max_length=24)),
        migrations.AddField(model_name="cvdocument", name="lifecycle_state", field=models.CharField(choices=[("draft", "Draft"), ("exported", "Exported"), ("archived", "Archived")], default="draft", max_length=16)),
        migrations.AddField(model_name="cvdocument", name="template_version", field=models.PositiveSmallIntegerField(default=1)),
        migrations.AddField(model_name="cvdocument", name="revision", field=models.PositiveIntegerField(default=1)),
    ]
