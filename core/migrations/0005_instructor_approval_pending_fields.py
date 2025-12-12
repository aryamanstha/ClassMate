# Generated migration for InstructorAccount pending registration fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_instructor_city_instructor_password_hash_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instructoraccount',
            name='instructor',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.instructor'),
        ),
        migrations.AddField(
            model_name='instructoraccount',
            name='pending_city',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='instructoraccount',
            name='pending_department',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='instructoraccount',
            name='pending_password_hash',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='instructoraccount',
            name='pending_phone',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='instructoraccount',
            name='pending_state',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='instructoraccount',
            name='pending_zip_code',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
    ]
