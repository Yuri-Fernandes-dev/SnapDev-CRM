from django.db import migrations, models
import uuid

class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='cost_total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Custo Total'),
        ),
        migrations.AddField(
            model_name='sale',
            name='profit',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Lucro'),
        ),
        migrations.AddField(
            model_name='sale',
            name='profit_margin',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Margem de Lucro'),
        ),
        migrations.AddField(
            model_name='sale',
            name='access_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AddField(
            model_name='saleitem',
            name='cost_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Preço de Custo'),
            preserve_default=False,
        ),
    ]