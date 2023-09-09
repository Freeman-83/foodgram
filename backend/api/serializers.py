import base64
import webcolors
from django.core.files.base import ContentFile

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from djoser.serializers import UserSerializer, UserCreateSerializer

from recipes.models import (Favorite,
                            Ingredient,
                            Recipe,
                            IngredientRecipe,
                            ShoppingCart,
                            Subscribe,
                            Tag,
                            TagRecipe)

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


class CustomUserSerializer(UserSerializer):
    "Кастомный сериализатор для отбображения пользователей."
    is_subscribed = serializers.BooleanField(
        default=False
    )
    
    class Meta:
        model = CustomUser
        fields = ('id',
                  'username',
                  'email',
                  'first_name',
                  'last_name',
                  'is_subscribed')


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


class TagRecipeSerializer(serializers.ModelSerializer):
    "Сериализатор тег-рецепт."
    id = serializers.IntegerField(
        source = 'tag.id'
    )

    class Meta:
        model = TagRecipe
        fields = ('id',
                  'tag',
                  'recipe')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    "Сериализатор ингредиент-рецепт."
    id = serializers.PrimaryKeyRelatedField(
        queryset = Ingredient.objects.all()
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


class RecipeListRetrieveSerializer(serializers.ModelSerializer):
    "Сериализатор для получения рецептов."
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='ingredients_used'
    )
    tags = TagSerializer(
        many=True
    )
    author = CustomUserSerializer()
    
    class Meta:
        model = Recipe
        fields = ('id',
                  'ingredients',
                  'tags',
                  'image',
                  'author',
                  'name',
                  'text',
                  'cooking_time')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    "Сериализатор для создания-обновления рецептов."
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='ingredients_used'
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    author = serializers.StringRelatedField(
        default=serializers.CurrentUserDefault(),
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = ('id',
                  'ingredients',
                  'tags',
                  'image',
                  'author',
                  'name',
                  'text',
                  'cooking_time')
        
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=['author', 'name']
            )
        ]

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients_used')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        for ingredient in ingredients_data:
            current_ingredient = ingredient.get('id')
            amount = ingredient.get('amount')

            IngredientRecipe.objects.create(ingredient=current_ingredient,
                                            recipe=recipe,
                                            amount=amount)

        recipe.tags.set(tags)

        return recipe


# class SubscribeSerializer(serializers.ModelSerializer):
#     "Сериализатор для подписки на автора."
#     author = serializers.SlugRelatedField(
#         queryset=CustomUser.objects.all(),
#         slug_field='username'
#     )
#     user = serializers.StringRelatedField(
#         default=serializers.CurrentUserDefault()
#     )

#     class Meta:
#         fields = ('user', 'author')
#         model = Subscribe
#         validators = [
#             UniqueTogetherValidator(
#                 queryset=Subscribe.objects.all(),
#                 fields=['user', 'author']
#             )
#         ]

#     def validate_author(self, value):
#         if value == self.context['request'].user:
#             raise serializers.ValidationError(
#                 'На себя, любимого, не подписываемся!'
#             )
#         return value

# class FavoriteSerializer(serializers.ModelSerializer):
#     "Сериализатор для избранного"
#     user = serializers.SlugRelatedField(
#         read_only=True, slug_field='username'
#     )
#     recipe = serializers.PrimaryKeyRelatedField(read_only=True)

#     class Meta:
#         fields = ('id', 'user', 'recipe')
#         model = Favorite
#         validators = [
#             UniqueTogetherValidator(
#                 queryset=Favorite.objects.all(),
#                 fields=['user', 'recipe']
#             )
#         ]



