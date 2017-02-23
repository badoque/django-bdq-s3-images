from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('s3images', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ExternalImage',
            name='size'
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
