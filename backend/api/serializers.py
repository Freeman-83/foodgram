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
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes'
        )

    def get_is_subscribed(self, author):
        user = self.context['request'].user
        if Subscribe.objects.filter(user=user, author=author):
            return True
        return False
    
    def get_recipes(self, user):
        recipes = user.recipes.values()
        return recipes


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


class IngredientRecipeSerializer(serializers.ModelSerializer):
    "Сериализатор ингредиент-рецепт."
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
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='ingredients_used'
    )
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
        ingredients_data = validated_data.pop('ingredients_used')
        tags_list = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        for ingredient in ingredients_data:
            current_ingredient = ingredient.get('id')
            amount = ingredient.get('amount')
            IngredientRecipe.objects.create(id=current_ingredient.id,
                                            ingredient=current_ingredient,
                                            recipe=recipe,
                                            amount=amount)
        recipe.tags.set(tags_list)

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

    def get_tags(self, recipe):
        return recipe.tags.values()
    
    def get_is_favorite(self, recipe):
        user = self.context['request'].user
        if Favorite.objects.filter(user=user, recipe=recipe):
            return True
        return False
    
    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        if ShoppingCart.objects.filter(user=user, recipe=recipe):
            return True
        return False
    

class RecipeShortSerializer(serializers.ModelSerializer):
    "Сериализатор для отображения в других контекстах."

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


# class RecipeListRetrieveSerializer(serializers.ModelSerializer):
#     "Сериализатор для получения рецептов."
#     ingredients = IngredientRecipeSerializer(
#         many=True,
#         source='ingredients_used'
#     )
#     tags = TagSerializer(
#         many=True,
#     )
#     author = CustomUserSerializer()

#     is_favorite = serializers.SerializerMethodField()
#     is_in_shopping_cart = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Recipe
#         fields = ('id',
#                   'ingredients',
#                   'tags',
#                   'image',
#                   'author',
#                   'name',
#                   'text',
#                   'cooking_time',
#                   'is_favorite',
#                   'is_in_shopping_cart')
        
#     def get_is_favorite(self, recipe):
#         user = self.context['request'].user
#         if Favorite.objects.filter(user=user, recipe=recipe):
#             return True
#         return False
    
#     def get_is_in_shopping_cart(self, recipe):
#         user = self.context['request'].user
#         if ShoppingCart.objects.filter(user=user, recipe=recipe):
#             return True
#         return False


class SubscribeSerializer(serializers.ModelSerializer):
    "Сериализатор для подписки на автора."
    author = CustomUserSerializer(
        read_only=True
    )

    class Meta:
        model = Subscribe
        fields = ('author',)

    def validate(self, data):
        request = self.context['request']
        user = request.user
        author = get_object_or_404(
            CustomUser, pk=self.context['view'].kwargs.get('id')
        )

        if request.method == 'POST':
            if user == author:
                raise ValidationError('На себя, любимого, не подписываемся!')
            elif Subscribe.objects.filter(user=user, author=author):
                raise ValidationError('Один автор - одна подписка!')
        elif request.method == 'DELETE':
            if not Subscribe.objects.filter(user=user, author=author):
                raise ValidationError('Сначала подписка - потом удаление!')
        return data
    
    # def to_representation(self, instance):
    #     # data = instance.author
    #     data = {
    #         'id': instance.author.id,
    #         'username': instance.author.username,
    #         'email': instance.author.email,
    #         'first_name': instance.author.first_name,
    #         'last_name': instance.author.last_name,
    #         'recipes': instance.author.recipes.values()
    #     }
    #     return data


class FavoriteSerializer(serializers.ModelSerializer):
    "Сериализатор для избранного"
    recipe = RecipeShortSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('recipe',)

    def validate(self, data):
        request = self.context['request']
        user = request.user
        recipe = get_object_or_404(
            Recipe, pk=self.context['view'].kwargs.get('id')
        )

        if request.method == 'POST':
            if user == recipe.author:
                raise ValidationError(
                    'Свои рецепты в избранное не добавляем!'
                )
            elif Favorite.objects.filter(user=user, recipe=recipe):
                raise ValidationError(
                    'Повторное добавление рецепта в избранное!'
                )
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    "Сериализатор для корзины покупок."
    recipe = RecipeShortSerializer(read_only=True)
    
    class Meta:
        model = ShoppingCart
        fields = ('recipe',)
        
    def validate(self, data):
        request = self.context['request']
        user = request.user
        recipe = get_object_or_404(
            Recipe, pk=self.context['view'].kwargs.get('id')
        )

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe):
                raise ValidationError(
                    'Повторное добавление рецепта в корзину!'
                )
        return data
