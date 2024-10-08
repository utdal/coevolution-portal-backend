# Generated by Django 5.0.7 on 2024-08-06 10:00

import api.modelutils
import datetime
import django.db.models.deletion
import functools
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='APIDataObject',
            fields=[
                ('id', models.UUIDField(default=api.modelutils.get_random_uuid, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('expires', models.DateTimeField(default=functools.partial(api.modelutils.get_future_date, *(datetime.timedelta(days=1),), **{}))),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CeleryTaskMeta',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('state', models.CharField(default='UNKNOWN', max_length=20)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('time_started', models.DateTimeField(auto_now_add=True)),
                ('time_ended', models.DateTimeField(null=True)),
                ('message', models.CharField(blank=True, max_length=255)),
                ('percent', models.FloatField(default=0)),
                ('successful', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='DirectCouplingAnalysis',
            fields=[
                ('apidataobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.apidataobject')),
                ('e_ij', api.modelutils.NdarrayField(null=True)),
                ('h_i', api.modelutils.NdarrayField(null=True)),
                ('ranked_di', api.modelutils.NdarrayField(null=True)),
                ('m_eff', models.IntegerField(null=True)),
            ],
            bases=('api.apidataobject',),
        ),
        migrations.CreateModel(
            name='MultipleSequenceAlignment',
            fields=[
                ('apidataobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.apidataobject')),
                ('fasta', models.FileField(null=True, upload_to=functools.partial(api.modelutils.get_user_spesific_path, *(), **{'subfolder': 'msa', 'suffix': '.fasta'}))),
                ('depth', models.IntegerField(default=0)),
                ('cols', models.IntegerField(default=0)),
                ('quality', models.IntegerField(choices=[(0, 'Na'), (1, 'Awful'), (2, 'Bad'), (3, 'Okay'), (4, 'Good'), (5, 'Great')], default=0)),
            ],
            bases=('api.apidataobject',),
        ),
        migrations.CreateModel(
            name='ContactMap',
            fields=[
                ('apidataobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.apidataobject')),
                ('pdb', models.CharField(blank=True, max_length=50)),
                ('map', api.modelutils.NdarrayField(null=True)),
                ('coupling_results', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.directcouplinganalysis')),
            ],
            bases=('api.apidataobject',),
        ),
        migrations.CreateModel(
            name='APITaskMeta',
            fields=[
                ('celerytaskmeta_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.celerytaskmeta')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            bases=('api.celerytaskmeta',),
        ),
    ]
