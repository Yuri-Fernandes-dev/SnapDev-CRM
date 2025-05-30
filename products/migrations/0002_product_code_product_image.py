# Generated by Django 4.2.20 on 2025-04-11 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='code',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='Código'),
        ),
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='products/', verbose_name='Imagem'),
        ),
    ]
