from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('meal_system', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            """
            DROP TABLE IF EXISTS meal_system_mealcategory;
            DROP TABLE IF EXISTS meal_system_mealitem;
            DROP TABLE IF EXISTS meal_system_mealitemimage;
            DROP TABLE IF EXISTS meal_system_mealcomponent;
            DROP TABLE IF EXISTS meal_system_mealcomponentimage;
            DROP TABLE IF EXISTS meal_system_mealitemcomponent;
            DROP TABLE IF EXISTS meal_system_mealcomponentitem;
            DROP TABLE IF EXISTS meal_system_hallmealcategorymeal;
            DROP TABLE IF EXISTS meal_system_hallmealorder;
            DROP TABLE IF EXISTS meal_system_hallmealorderitem;
            """,
            """
            -- No reverse SQL needed as we're dropping tables
            SELECT 1;
            """
        ),
    ]
