import base64
import webcolors
from django.db.models import F
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from djoser.serializers import UserSerializer, UserCreateSerializer

from recipes.models import (Favorite,
                            Ingredient,
                            Recipe,
                            IngredientRecipe,
                            ShoppingCart,
                            Subscribe,
                            Tag)

from users.models import CustomUser


class Base64ImageField(serializers.ImageField):
    "Кастомное поле для изображений."
    
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


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
        fields = ('id', 'name', 'image', 'cooking_time')


class CustomUserSerializer(UserSerializer):
    "Кастомный сериализатор для пользователей."
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed'
        )

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
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, author):
        user = self.context['request'].user
        return Subscribe.objects.filter(user=user, author=author).exists()
    
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
    is_favorite = serializers.SerializerMethodField()
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
                  'is_favorite',
                  'is_in_shopping_cart')

        validators = [
            UniqueTogetherValidator(queryset=Recipe.objects.all(),
                                    fields=['author', 'name'])
        ]

    def validate(self, data):
        tags_list = self.initial_data.get('tags')
        ingredients_data = self.initial_data.get('ingredients')

        if tags_list:
            for tag_id in tags_list:
                if not Tag.objects.filter(id=tag_id).exists():
                    raise ValidationError('Несуществующий тег!')
        else:
            raise ValidationError(
                'Необходимо указать минимум один тег!'
            )

        if ingredients_data:
            for ingredient in ingredients_data:
                ingredient_id = ingredient.get('id')
                amount = ingredient.get('amount', 0)
                if not Ingredient.objects.filter(id=ingredient_id).exists():
                    raise ValidationError('Несуществующий ингредиент!')
                if not amount or type(amount) is not int:
                    raise ValidationError(
                        'Укажите количество используемого ингредиента '
                        '(натуральное число не менее 1)'
                    )

        else:
            raise ValidationError(
                'Необходимо указать минимум один ингредиент!'
            )

        data.update({'tags': tags_list,
                     'ingredients': ingredients_data})

        return data

    def create(self, validated_data):
        tags_list = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        
        recipe = Recipe.objects.create(**validated_data)
        
        recipe.tags.set(tags_list)

        for ingredient in ingredients_data:
            current_ingredient = get_object_or_404(
                Ingredient, pk=ingredient.get('id')
            )
            amount = ingredient.get('amount')
            IngredientRecipe.objects.create(ingredient=current_ingredient,
                                            recipe=recipe,
                                            amount=amount)
        return recipe
    
    def update(self, instance, validated_data):

        tags_list = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        instance = super().update(instance, validated_data)

        instance.save()

        if tags_list:
            instance.tags.clear()
            instance.tags.set(tags_list)

        if ingredients_data:
            instance.ingredients.clear()
            for ingredient in ingredients_data:
                current_ingredient = get_object_or_404(
                    Ingredient, pk=ingredient.get('id')
                )
                amount = ingredient.get('amount')

                IngredientRecipe.objects.create(ingredient=current_ingredient,
                                                recipe=instance,
                                                amount=amount)

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
    
    def get_is_favorite(self, recipe):
        user = self.context['request'].user.id
        return Favorite.objects.filter(user=user, recipe=recipe).exists()
    
    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user.id
        return ShoppingCart.objects.filter(user=user, recipe=recipe).exists()


# class ShoppingCartSerializer(serializers.ModelSerializer):
#     "Сериализатор для корзины покупок."
#     recipe = RecipeInfoSerializer(read_only=True)
    
#     class Meta:
#         model = ShoppingCart
#         fields = ('recipe',)
        
#     def validate(self, data):
#         request = self.context['request']
#         user = request.user
#         recipe = get_object_or_404(
#             Recipe, pk=self.context['view'].kwargs.get('id')
#         )

#         if request.method == 'POST':
#             if ShoppingCart.objects.filter(user=user, recipe=recipe):
#                 raise ValidationError(
#                     'Повторное добавление рецепта в корзину!'
#                 )
#         return data
