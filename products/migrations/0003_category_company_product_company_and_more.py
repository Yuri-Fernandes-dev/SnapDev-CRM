# Generated by Django 4.2.20 on 2025-04-13 17:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_company_created_at_company_is_active_company_owner_and_more'),
        ('products', '0002_product_code_product_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='company',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='core.company', verbose_name='Empresa'),
        ),
        migrations.AddField(
            model_name='product',
            name='company',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='core.company', verbose_name='Empresa'),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('company', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='product',
            unique_together={('company', 'code'), ('company', 'barcode')},
        ),
    ]
