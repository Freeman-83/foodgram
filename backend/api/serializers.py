import base64
import webcolors
from django.core.files.base import ContentFile

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from djoser.serializers import UserSerializer, UserCreateSerializer

from recipes.models import (Favorite,
                            Ingredient,
                            Recipe,
                            ShoppingCart,
                            Subscribe,
                            Tag)

from user.models import CustomUser


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


class CustomUserSerializer(UserSerializer):
    "Кастомный сериализатор для отбображения пользователей."
    
    class Meta:
        fields = ('id',
                  'username',
                  'email',
                  'first_name',
                  'last_name')
        model = CustomUser


class RegisterUserSerializer(UserCreateSerializer):
    "Кастомный сериализатор для регистрации пользователя."
    
    class Meta:
        fields = ('id',
                  'username',
                  'email',
                  'first_name',
                  'last_name',
                  'password')
        model = CustomUser


class TagSerializer(serializers.ModelSerializer):
    "Сериализатор для тегов."
    color = Hex2NameColor()

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    "Сериализатор для ингредиентов."

    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class RecipeSerializer(serializers.ModelSerializer):
    "Сериализатор для рецептов."
    tag = TagSerializer(many=True)
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True
    )
    ingredients = IngredientSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        fields = ('id', 'tag', 'author', 'ingredients', 'name',
                  'image', 'text', 'cooking_time')
        model = Recipe
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=['author', 'name']
            )
        ]


class FavoriteSerializer(serializers.ModelSerializer):
    "Сериализатор для избранного"
    user = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        fields = ('id', 'user', 'recipe')
        model = Favorite
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe']
            )
        ]


class SubscribeSerializer(serializers.ModelSerializer):
    "Сериализатор для подписки на автора."
    author = serializers.SlugRelatedField(
        queryset=CustomUser.objects.all(), slug_field='username'
    )
    user = serializers.StringRelatedField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        fields = ('user', 'author')
        model = Subscribe
        validators = [
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=['user', 'author']
            )
        ]

    def validate_author(self, value):
        if value == self.context['request'].user:
            raise serializers.ValidationError(
                'Запрет подписки пользователя на самого себя!'
            )
        return value
