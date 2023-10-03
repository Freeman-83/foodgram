import webcolors

from django.db.models import F
from django.shortcuts import get_object_or_404

from drf_extra_fields.fields import Base64ImageField

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from djoser.serializers import UserSerializer, UserCreateSerializer

from recipes.models import (Ingredient,
                            Recipe,
                            IngredientRecipe,
                            Subscribe,
                            Tag)

from users.models import CustomUser

from .utils import get_validated_ingredients, get_validated_tags


class Hex2NameColor(serializers.Field):
    "Кастомное поле для преобразования цветового кода."

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class RecipeContextSerializer(serializers.ModelSerializer):
    "Сериализатор для отображения профиля рецепта в других контекстах."

    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'image',
                  'cooking_time')


class CustomUserSerializer(UserSerializer):
    "Кастомный сериализатор для пользователей."
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('id',
                  'username',
                  'email',
                  'first_name',
                  'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, author):
        user = self.context['request'].user.id
        return Subscribe.objects.filter(user=user, author=author).exists()


class RegisterUserSerializer(UserCreateSerializer):
    "Кастомный сериализатор для регистрации пользователя."

    class Meta:
        model = CustomUser
        fields = ('id',
                  'username',
                  'email',
                  'first_name',
                  'last_name',
                  'password')


class CustomUserContextSerializer(UserSerializer):
    """ Кастомный сериализатор для отображения профиля пользователя
    в других контекстах."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeContextSerializer(many=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('id',
                  'username',
                  'email',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'recipes',
                  'recipes_count')

    def get_is_subscribed(self, author):
        user = self.context['request'].user
        return user.subscriptions.filter(author=author).exists()

    def get_recipes_count(self, author):
        return author.recipes.all().count()


class TagSerializer(serializers.ModelSerializer):
    "Сериализатор для тегов."
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id',
                  'name',
                  'color',
                  'slug')


class IngredientSerializer(serializers.ModelSerializer):
    "Сериализатор для ингредиентов."

    class Meta:
        model = Ingredient
        fields = ('id',
                  'name',
                  'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):
    "Сериализатор для создания-обновления рецептов."
    ingredients = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    image = Base64ImageField()
    author = CustomUserSerializer(
        default=serializers.CurrentUserDefault()
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id',
                  'ingredients',
                  'tags',
                  'image',
                  'author',
                  'name',
                  'text',
                  'cooking_time',
                  'is_favorited',
                  'is_in_shopping_cart')

        validators = [
            UniqueTogetherValidator(queryset=Recipe.objects.all(),
                                    fields=['author', 'name'])
        ]

    def validate_cooking_time(self, value):
        cooking_time = value
        if not cooking_time or int(cooking_time) < 1:
            raise ValidationError(
                'Укажите время приготовления блюда в минутах '
                '(натуральное число не менее 1)'
            )

        return value

    # Убрал валидацию на уровне поля в utils,
    # потому что иначе ломалась логика с initial_data

    def validate(self, data):
        ingredients_data = self.initial_data.get('ingredients')
        tags_list = self.initial_data.get('tags')

        ingredients = get_validated_ingredients(ingredients_data, Ingredient)
        tags = get_validated_tags(tags_list, Tag)

        data.update({'ingredients': ingredients,
                     'tags': tags})

        return data

    def create_ingredients(self, recipe, ingredients):
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient, pk=ingredient.get('id')
            )
            amount = ingredient.get('amount')
            IngredientRecipe.objects.create(ingredient=current_ingredient,
                                            recipe=recipe,
                                            amount=amount)

    def create(self, validated_data):
        tags_list = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_list)

        self.create_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        tags_list = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.save()

        instance.tags.clear()
        instance.tags.set(tags_list)

        instance.ingredients.clear()
        self.create_ingredients(instance, ingredients_data)

        return instance

    def get_ingredients(self, recipe):
        return recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipes_used__amount')
        )

    def get_tags(self, recipe):
        return recipe.tags.values()

    # Решил оставить первый предложенный тобой вариант с related_name.
    # Он показался мне более наглядным.
    # Подумал, что если выносить проверку данных полей
    # в отдельную функцию, то логично было бы захватить и подписки.
    # Но в таком случае реализация выглядит массивнее, чем сейчас.
    # Если все же лучше вынести - сделаю без проблем

    def get_is_favorited(self, recipe):
        user = self.context['request'].user
        return user.favorite_recipes.filter(recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        return user.shopping_carts.filter(recipe=recipe).exists()
