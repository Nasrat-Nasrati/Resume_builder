from django.db import migrations, models
import modules.resumes.models


def default_design_options():
    return {"theme": "blue-teal", "font": "sans", "layout": "classic"}


class Migration(migrations.Migration):
    dependencies = [("resumes", "0009_cvdocument_template_key")]
    operations = [
        migrations.AddField(
            model_name="cvdocument",
            name="design_options",
            field=models.JSONField(default=modules.resumes.models.default_design_options),
        ),
    ]
