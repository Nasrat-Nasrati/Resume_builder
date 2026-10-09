from django.db import migrations

def normalize(apps, schema_editor):
    CV = apps.get_model("resumes", "CVDocument")
    for doc in CV.objects.iterator():
        data = doc.snapshot or {}
        if "profile" in data:
            data["personal"] = {**data.pop("profile"), **data.get("personal", {})}
        for key in ("experience", "education"):
            if isinstance(data.get(key), dict):
                data[key] = data[key].get(key, [])
        if isinstance(data.get("skills"), dict):
            nested = data.pop("skills")
            data.update(nested)
        for key in ("experience", "education", "languages"):
            for row in data.get(key, []):
                if isinstance(row, dict): row.pop("sort_order", None)
        doc.snapshot = data
        doc.selected_sections = ["personal" if key == "profile" else key for key in doc.selected_sections]
        doc.save(update_fields=["snapshot", "selected_sections"])

class Migration(migrations.Migration):
    dependencies = [("resumes", "0007_write_revision")]
    operations = [migrations.RunPython(normalize, migrations.RunPython.noop)]
