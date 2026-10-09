from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="PageViewDaily",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("page_date", models.DateField()),
                ("path", models.CharField(max_length=32)),
                ("view_count", models.PositiveIntegerField(default=0)),
            ],
            options={
                "constraints": [models.UniqueConstraint(fields=("page_date", "path"), name="unique_daily_public_page_views")],
                "indexes": [models.Index(fields=["page_date", "path"], name="daily_page_view_date_idx")],
            },
        ),
    ]
