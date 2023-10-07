from django.db.models import F, Prefetch
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
                            IngredientRecipe,
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

from .paginators import CustomPagination

from .permissions import IsAdminOrAuthorOrReadOnly

from .utils import create_relation, delete_relation


class CustomUserViewSet(UserViewSet):
    "Кастомный вьюсет для пользователей."
    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [permissions.IsAuthenticated, ]
        return super().get_permissions()

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated, ])
    def subscribe(self, request, id):
        author = get_object_or_404(CustomUser, pk=id)
        if request.user != author:
            if request.method == 'POST':
                return create_relation(request,
                                       CustomUser,
                                       Subscribe,
                                       id,
                                       CustomUserContextSerializer,
                                       field='author')
            return delete_relation(request,
                                   CustomUser,
                                   Subscribe,
                                   id,
                                   field='author')
        return Response(
            data={'errors': 'Подписка на самого себя запрещена'},
            status=status.HTTP_400_BAD_REQUEST
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
    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related(
        'tags',
        Prefetch(
            'ingredients_used',
            queryset=IngredientRecipe.objects.select_related('ingredient')
        )
    ).all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAdminOrAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated, ])
    def favorite(self, request, pk):
        if request.method == 'POST':
            return create_relation(request,
                                   Recipe,
                                   Favorite,
                                   pk,
                                   RecipeContextSerializer,
                                   field='recipe')
        return delete_relation(request,
                               Recipe,
                               Favorite,
                               pk,
                               field='recipe')

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return create_relation(request,
                                   Recipe,
                                   ShoppingCart,
                                   pk,
                                   RecipeContextSerializer,
                                   field='recipe')
        return delete_relation(request,
                               Recipe,
                               ShoppingCart,
                               pk,
                               field='recipe')

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
