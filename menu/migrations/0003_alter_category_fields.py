from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0002_remove_cart_menu_cart_user_id_ba9ab7_idx_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=120, unique=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(blank=True, max_length=140, unique=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="vendor",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name="menu_categories", to="vendors.vendor"),
        ),
        migrations.RemoveConstraint(
            model_name="category",
            name="unique_menu_category_slug_per_vendor",
        ),
        migrations.RunSQL(
            sql="UPDATE menu_category SET vendor_id = NULL WHERE vendor_id IS NULL;",
            reverse_sql="SELECT 1;",
        ),
    ]
