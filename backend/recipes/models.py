from django.core.validators import MinValueValidator
from django.db import models

from colorfield.fields import ColorField

from users.models import CustomUser


class Tag(models.Model):
    "Модель тега."
    name = models.CharField('Tag', unique=True, max_length=200)
    slug = models.SlugField('Slug', unique=True, max_length=200)
    color = ColorField('Цвет', unique=True, max_length=7)

    class Meta:
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    "Модель ингредиента."
    name = models.CharField('Ингредиент', max_length=200)
    measurement_unit = models.CharField('Ед.изм', max_length=200)

    class Meta:
        ordering = ['name']
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    "Модель рецепта."
    name = models.CharField('Название', max_length=200)
    text = models.TextField('Описание')
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    image = models.ImageField('Изображение', upload_to='recipes/image/')
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
        verbose_name='Tags'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(1)]
    )

    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        default_related_name = 'recipes'

    def __str__(self):
        return self.name


class TagRecipe(models.Model):
    "Модель отношений тег-рецепт."
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='recipes_used'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='tags_used'
    )

    class Meta:
        ordering = ['tag']
        constraints = [
            models.UniqueConstraint(fields=['tag', 'recipe'],
                                    name='unique_tag_recipe')
        ]

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class IngredientRecipe(models.Model):
    "Модель отношений ингредиент-рецепт."
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipes_used'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_used'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ['ingredient']
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='unique_ingredient_recipe')
        ]

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class Subscribe(models.Model):
    "Модель подписок."
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribers'
    )

    class Meta:
        ordering = ['author']
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_subscribe')
        ]

    def __str__(self):
        return f'{self.user} {self.author}'


class Favorite(models.Model):
    "Модель избранных рецептов."
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorite_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorite_for_users'
    )

    class Meta:
        ordering = ['recipe']
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_favorite')
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class ShoppingCart(models.Model):
    "Модель списка покупок."
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_carts'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart_for_users'
    )

    class Meta:
        ordering = ['recipe']
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_recipe_for_shopping')
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'
