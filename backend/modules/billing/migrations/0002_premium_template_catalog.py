from django.db import migrations


def update_premium_templates(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.filter(code="premium").update(allowed_templates=["public-service-v1", "professional-v1", "ats-v1"])


class Migration(migrations.Migration):
    dependencies = [("billing", "0001_initial")]
    operations = [migrations.RunPython(update_premium_templates, migrations.RunPython.noop)]
