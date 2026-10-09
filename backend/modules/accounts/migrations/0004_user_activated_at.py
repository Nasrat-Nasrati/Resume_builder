from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_user_pending_email")]
    operations = [
        migrations.AddField(
            model_name="user",
            name="activated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
