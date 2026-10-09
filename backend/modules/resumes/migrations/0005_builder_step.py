from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("resumes", "0004_artifacts_and_export_charges")]
    operations = [migrations.AddField(model_name="cvdocument", name="builder_step", field=models.PositiveSmallIntegerField(default=1)), migrations.AddField(model_name="cvdocument", name="last_completed_step", field=models.PositiveSmallIntegerField(default=0))]
