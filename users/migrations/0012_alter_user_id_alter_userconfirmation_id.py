# Generated by Django 4.2.7 on 2023-12-15 10:41

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_alter_user_id_alter_userconfirmation_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.UUIDField(default=uuid.UUID('e027a9b2-6ca3-4c17-bc0a-1a5b6a4d42fa'), primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='userconfirmation',
            name='id',
            field=models.UUIDField(default=uuid.UUID('e027a9b2-6ca3-4c17-bc0a-1a5b6a4d42fa'), primary_key=True, serialize=False),
        ),
    ]
