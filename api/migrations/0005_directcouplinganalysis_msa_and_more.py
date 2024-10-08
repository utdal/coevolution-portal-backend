# Generated by Django 5.1.1 on 2024-09-03 23:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_structurecontacts'),
    ]

    operations = [
        migrations.AddField(
            model_name='directcouplinganalysis',
            name='msa',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.multiplesequencealignment'),
        ),
        migrations.AddField(
            model_name='multiplesequencealignment',
            name='seed',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.seedsequence'),
        ),
    ]
