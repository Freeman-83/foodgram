# Generated by Django 3.2.20 on 2023-09-05 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_auto_20230905_1615'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='tag',
        ),
        migrations.AddField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(related_name='recipes', through='recipes.TagRecipe', to='recipes.Tag', verbose_name='Tags'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='ingredients',
            field=models.ManyToManyField(related_name='recipes', through='recipes.IngredientRecipe', to='recipes.Ingredient', verbose_name='Ингредиенты'),
        ),
    ]
