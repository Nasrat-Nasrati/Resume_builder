from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_user_phone")]
    operations = [migrations.AddField(model_name="user", name="pending_email", field=models.EmailField(blank=True, max_length=254))]
