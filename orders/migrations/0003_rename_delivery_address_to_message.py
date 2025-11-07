# Generated migration to rename delivery_address to delivery_message

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_order_product_category_snapshot_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="order",
            old_name="delivery_address",
            new_name="delivery_message",
        ),
    ]
