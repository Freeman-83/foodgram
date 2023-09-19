import base64
import webcolors
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
        user = self.context['request'].user
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
    recipes_count = serializers.IntegerField(read_only=True)

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


class IngredientRecipeSerializer(serializers.ModelSerializer):
    "Сериализатор для ингредиента-рецепта."
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    name = serializers.CharField(
        source='ingredient.name',
        required=False
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        required=False
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id',
                  'name',
                  'measurement_unit',
                  'amount')


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

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_list = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_list)

        for ingredient in ingredients_data:
            current_ingredient = Ingredient.objects.get(pk=ingredient.get('id'))
            amount = ingredient.get('amount')
            IngredientRecipe.objects.create(ingredient=current_ingredient,
                                            recipe=recipe,
                                            amount=amount)
        return recipe
    
    # def update(self, instance, validated_data):
    #     if 'tags' in self.initial_data:
    #         tags_list = validated_data.pop('tags')
    #         instance.tags.set(tags_list)

    #     if 'ingredients_used' in self.initial_data:
    #         ingredients_data = validated_data.pop('ingredients_used')
            
    #         # for ingredient in ingredients_data:
    #         instance.ingredients.set(ingredients_data)

    #         instance = Recipe.objects.update_or_create(**validated_data)

    #     return instance

    def get_ingredients(self, recipe):
        return recipe.ingredients.values()

    def get_tags(self, recipe):
        return recipe.tags.values()
    
    def get_is_favorite(self, recipe):
        user = self.context['request'].user
        return Favorite.objects.filter(user=user, recipe=recipe).exists()
    
    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
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
