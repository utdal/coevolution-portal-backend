# Generated by Django 5.0.7 on 2024-08-15 19:42

import api.modelutils
import django.db.models.deletion
import functools
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_apitaskmeta_expires'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeedSequence',
            fields=[
                ('apidataobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.apidataobject')),
                ('name', models.CharField(max_length=200)),
                ('fasta', models.FileField(upload_to=functools.partial(api.modelutils.get_user_spesific_path, *(), **{'subfolder': 'seeds', 'suffix': '.fasta'}))),
            ],
            bases=('api.apidataobject',),
        ),
        migrations.CreateModel(
            name='MappedDi',
            fields=[
                ('apidataobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.apidataobject')),
                ('protein_name', models.CharField(max_length=200)),
                ('mapped_di', api.modelutils.NdarrayField()),
                ('dca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.directcouplinganalysis')),
                ('seed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.seedsequence')),
            ],
            bases=('api.apidataobject',),
        ),
    ]
