from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from djoser.views import UserViewSet

from .filters import IngredientFilterSet, RecipeFilterSet

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework import pagination, permissions, viewsets

from recipes.models import (Favorite,
                            Ingredient,
                            Recipe,
                            ShoppingCart,
                            Subscribe,
                            Tag)

from users.models import CustomUser

from .serializers import (CustomUserSerializer,
                          CustomUserContextSerializer,
                          IngredientSerializer,
                          RecipeSerializer,
                          RecipeContextSerializer,
                          TagSerializer)

from .permissions import IsAdminOrAuthorOrReadOnly


class CustomUserViewSet(UserViewSet):
    "Кастомный вьюсет для пользователей."
    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = pagination.PageNumberPagination

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated, ])
    def subscribe(self, request, id=None):
        author = get_object_or_404(CustomUser, pk=id)
        subscribe_obj = Subscribe.objects.filter(user=request.user,
                                                 author=author)

        if request.method == 'POST':
            if not subscribe_obj.exists():
                if author != request.user:
                    Subscribe.objects.create(user=request.user,
                                             author=author)
                    serializer = CustomUserContextSerializer(
                        author, context={'request': request}
                    )
                    return Response(
                        serializer.data,
                        status=status.HTTP_201_CREATED)
                return Response(
                    data={'errors': 'Подписка на себя запрещена!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                data={'errors': 'Повторная подписка на пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            if subscribe_obj.exists():
                subscribe_obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                data={'errors': 'Подписка отсутствует'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False,
            permission_classes=[permissions.IsAuthenticated, ])
    def subscriptions(self, request):
        subscribers_data = CustomUser.objects.filter(
            subscribers__user=request.user
        )
        page = self.paginate_queryset(subscribers_data)
        serializer = CustomUserContextSerializer(
            page, many=True, context={'request': request}
        )

        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    "Вьюсет для Тегов."
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    "Вьюсет для ингредиентов."
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilterSet


class RecipeViewSet(viewsets.ModelViewSet):
    "Вьюсет для рецептов."
    queryset = Recipe.objects.select_related('author').all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAdminOrAuthorOrReadOnly,)
    pagination_class = pagination.PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated, ])
    def favorite(self, request, pk=None):

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)
            favorite_obj = Favorite.objects.filter(user=request.user,
                                                   recipe=recipe)
            if not favorite_obj.exists():
                Favorite.objects.create(user=request.user,
                                        recipe=recipe)
                serializer = RecipeContextSerializer(recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(
                data={'errors': 'Повторное добавление рецепта в избранное'},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, pk=pk)
            favorite_obj = Favorite.objects.filter(user=request.user,
                                                   recipe=recipe)
            if favorite_obj.exists():
                favorite_obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                data={'errors': 'Рецепт в избранном отсутствует'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart_obj = ShoppingCart.objects.filter(user=request.user,
                                                        recipe=recipe)
        if request.method == 'POST':
            if not shopping_cart_obj.exists():
                ShoppingCart.objects.create(user=request.user,
                                            recipe=recipe)
                serializer = RecipeContextSerializer(recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(
                data={'errors': 'Повторное добавление рецепта в корзину!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            if shopping_cart_obj.exists():
                shopping_cart_obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(data={'errors': 'Рецепт в корзине отсутствует'},
                            status=status.HTTP_404_NOT_FOUND)

    @action(detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request, *args, **kwargs):
        recipes = Recipe.objects.filter(
            in_shopping_cart_for_users__user=request.user
        )

        shopping_cart = {}

        for recipe in recipes:
            ingredients = recipe.ingredients.values(
                    'name',
                    'measurement_unit',
                    amount=F('recipes_used__amount')
                )

            for ingredient in ingredients:
                name = (f"{ingredient['name']} "
                        f"({ingredient['measurement_unit']}) - ")
                amount = ingredient['amount']
                shopping_cart[name] = shopping_cart.get(name, 0) + amount

        shopping_list = 'Список покупок:\n'

        for key, value in shopping_cart.items():
            shopping_list += f'{key}{value}\n'

        filename = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response
