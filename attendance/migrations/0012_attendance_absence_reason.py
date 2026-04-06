from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0011_update_setting_sms_default_messages"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendance",
            name="absence_reason",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="결석 사유"),
        ),
    ]
