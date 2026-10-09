from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("exports", "0003_exportreservation")]
    operations = [
        migrations.AlterField(
            model_name="exportjob",
            name="format",
            field=models.CharField(choices=[("pdf", "PDF"), ("docx", "Word document")], default="pdf", max_length=8),
        ),
    ]
