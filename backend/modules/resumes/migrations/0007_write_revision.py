from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [("resumes", "0006_cv_photo")]
    operations = [
        migrations.AddField(model_name="cvdocument", name="last_write_id", field=models.UUIDField(blank=True, null=True)),
        migrations.AddField(model_name="cvdocument", name="last_write_hash", field=models.CharField(blank=True, max_length=64)),
    ]
