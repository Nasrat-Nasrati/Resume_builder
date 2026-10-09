from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("resumes", "0002_cv_document_lifecycle")]
    operations = [migrations.AddField(model_name="cvdocument", name="state_before_archive", field=models.CharField(blank=True, choices=[("draft", "Draft"), ("exported", "Exported"), ("archived", "Archived")], max_length=16))]
