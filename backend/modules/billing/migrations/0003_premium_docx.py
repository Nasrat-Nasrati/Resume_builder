from django.db import migrations


def enable_premium_docx(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.filter(code="premium").update(allowed_formats=["pdf", "docx"])


class Migration(migrations.Migration):
    dependencies = [("billing", "0002_premium_template_catalog")]
    operations = [migrations.RunPython(enable_premium_docx, migrations.RunPython.noop)]
