
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_productmodel_product_product_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='brand',
        ),
        migrations.RemoveField(
            model_name='product',
            name='description',
        ),
        migrations.RemoveField(
            model_name='product',
            name='subcategory',
        ),
        migrations.AlterField(
            model_name='product',
            name='product_model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='color_variants', to='products.productmodel'),
        ),
    ]
