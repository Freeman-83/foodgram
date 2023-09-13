import base64
import webcolors
from django.core.files.base import ContentFile

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
    # is_subscribed = serializers.BooleanField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            # 'is_subscribed',
            # 'recipes'
        )


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


# class TagRecipeSerializer(serializers.ModelSerializer):
#     "Сериализатор тег-рецепт."
#     id = serializers.IntegerField(
#         source = 'tag.id'
#     )
#     name = serializers.CharField(
#         source = 'tag.name',
#         required=False
#     )
#     slug = serializers.SlugField(
#         source = 'tag.slug',
#          required=False
#     )
#     color = serializers.CharField(
#         source = 'tag.color',
#         required=False
#     )

#     class Meta:
#         model = TagRecipe
#         fields = ('id',
#                 #   'name',
#                 #   'slug',
#                 #   'color',
#                   'tag',
#                   'recipe',)


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

    # TagRecipeSerializer(
    #     # default=None,
    #     many=True,
    #     source='tags_used'
    # )
    
    image = Base64ImageField()
    author = CustomUserSerializer(
        default=serializers.CurrentUserDefault()
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
            IngredientRecipe.objects.create(ingredient=current_ingredient,
                                            recipe=recipe,
                                            amount=amount)
            
        # for tag in tags_list:
        #     TagRecipe.objects.create(tag=tag,
        #                              recipe=recipe)

        recipe.tags.set(tags_list)

        return recipe


class RecipeListRetrieveSerializer(serializers.ModelSerializer):
    "Сериализатор для получения рецептов."
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='ingredients_used'
    )
    tags = TagSerializer(
        many=True,
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


class SubscribeSerializer(serializers.ModelSerializer):
    "Сериализатор для подписки на автора."
    # id = serializers.IntegerField(source='author.id', read_only=True)
    # username = serializers.CharField(source='author.username', read_only=True)
    # email = serializers.EmailField(source='author.email', read_only=True)
    # first_name = serializers.CharField(source='author.first_name', read_only=True)
    # last_name = serializers.CharField(source='author.last_name', read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    # recipes = serializers.PrimaryKeyRelatedField(
    #     many=True, source='author.recipes', read_only=True)

    class Meta:
        model = Subscribe
        fields = (#'id',
                #   'username',
                #   'email',
                #   'first_name',
                #   'last_name',
                #   'recipes'
                  'is_subscribed',)
        # read_only_fields = ('id',
        #                     'username',
        #                     'email',
        #                     'first_name',
        #                     'last_name',
        #                     'recipes')

    def validate(self, data):
        request = self.context['request']
        user = request.user
        author = self.context['view'].kwargs.get('id')
        
        if request.method == 'POST':
            if Subscribe.objects.filter(user=user, author=author):
                raise ValidationError('Один автор - одна подписка!')
            elif Subscribe.objects.filter(user=author):
                raise ValidationError('На себя, любимого, не подписываемся!')
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    "Сериализатор для избранного"
    is_favorite = serializers.BooleanField(read_only=True)

    class Meta:
        model = Favorite
        fields = ('is_favorite',)

        def validate(self, data):
            request = self.context['request']
            user = request.user
            recipe = self.context['view'].kwargs.get('id')
            
            if request.method == 'POST':
                if Favorite.objects.filter(user=user, recipe=recipe):
                    raise ValidationError(
                        'Ошибка: повторное добавление рецепта в избранное!'
                    )
                elif Favorite.objects.filter(user=recipe):
                    raise ValidationError(
                        'Свои рецепты в избранное не добавляем!'
                    )
            return data

# Нужен ли отдельный сериализатор для Корзины покупок???
