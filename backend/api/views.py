from django.db.models import Count
from django.shortcuts import get_object_or_404

from djoser.views import UserViewSet

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework import filters, mixins, pagination, permissions, viewsets

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
                        # ShoppingCartSerializer,
                          TagSerializer)

# from .permissions import AuthorOrReadOnly


# class ListCreateDeleteViewSet(mixins.ListModelMixin,
#                               mixins.CreateModelMixin,
#                               mixins.DestroyModelMixin,
#                               viewsets.GenericViewSet):
#     pass

class CustomUserViewSet(UserViewSet):
    "Кастомный вьюсет для пользователей."
    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.prefetch_related(
            'recipes'
        ).annotate(
            recipes_count=Count('recipes')
        ).all()
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = pagination.PageNumberPagination
    # filter_backends = (DjangoFilterBackend,)
    # filterset_class = TitleFilterSet


    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated,])
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
                data = {'errors': 'Повторная подписка на пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            if subscribe_obj.exists():
                subscribe_obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                data = {'errors': 'Подписка отсутствует'},
                status=status.HTTP_404_NOT_FOUND
            )


    @action(detail=False,
            permission_classes=[permissions.IsAuthenticated,])
    def subscriptions(self, request):
        user = self.request.user
        subscribers_data = CustomUser.objects.filter(subscribers__user=user)
        page = self.paginate_queryset(subscribers_data)
        if page:
            serializer = CustomUserContextSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = CustomUserContextSerializer(
                subscribers_data, many=True, context={'request': request}
            )
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
            'author'
        ).prefetch_related(
            'tags', 'ingredients'
        ).all()
    serializer_class = RecipeSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = pagination.PageNumberPagination
    # filter_backends = (DjangoFilterBackend,)
    # filterset_class = TitleFilterSet

    def perform_update(self, serializer):
        serializer.save(**self.request.data)

    def perform_create(self, serializer):
        ingredients = self.request.data['ingredients']
        tags = self.request.data['tags']
        serializer.save(ingredients=ingredients,
                        tags=tags,
                        author=self.request.user)
        
    # def update(self, request, *args, **kwargs):
    #     kwargs['partial'] = True
    #     return super().update(request, *args, **kwargs)

    # Не настроено изменение ингредиентов!

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated,])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite_obj = Favorite.objects.filter(user=request.user,
                                               recipe=recipe)

        if request.method == 'POST':
            if not favorite_obj.exists():
                Favorite.objects.create(user=request.user,
                                        recipe=recipe)
                serializer = RecipeContextSerializer(recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(
                data = {'errors': 'Повторное добавление рецепта в избранное'},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            if favorite_obj.exists():
                favorite_obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                data = {'errors': 'Рецепт в избранном отсутствует'},
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
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                data={'errors': 'Повторное добавление рецепта в корзину!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            if shopping_cart_obj.exists():
                shopping_cart_obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(data = {'errors': 'Рецепт в корзине отсутствует'},
                            status=status.HTTP_404_NOT_FOUND)


        @action(detail=False)
        def download_shopping_cart(self, request):
            pass


# class SubscribeViewSet(viewsets.ModelViewSet):
#     serializer_class = SubscribeSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ('user__username', 'author__username')
    # http_method_names = ('get', 'post', 'delete')
    # lookup_field = 'subscribe'

    # def get_serializer_class(self):
    #     if self.action == 'list':
    #         return CustomUserSerializer
    #     return super().get_serializer_class()

    # def get_queryset(self):
    #     queryset = self.request.user.subscriptions.select_related(
    #         'user', 'author'
    #     ).all()
    #     return queryset

    # def perform_create(self, serializer):
    #     author = get_object_or_404(CustomUser, pk=self.kwargs.get('id'))
    #     serializer.save(user=self.request.user,
    #                     author=author)
        
    # def destroy(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     self.perform_destroy(instance)
    #     return Response(status=status.HTTP_204_NO_CONTENT)

    # def perform_destroy(self, instance):
    #     instance.delete()

    # @action(methods=['post', 'delete'], detail=True)
    # def subscribe(self, request):
    #     author = get_object_or_404(CustomUser, pk=self.kwargs.get('id'))
    #     obj = CustomUser.objects.filter(user=request.user,
    #                                     author=author)
    #     serializer = self.get_serializer(obj, many=True)
    #     return Response(serializer.data)

    # def perform_destroy(self, instance):
    #     if self.request.method == 'delete':
    #         instance = self.get_object()
    #         instance.delete()
    #     return super().perform_destroy(instance)

    # Не настроено удаление
        
# class ShoppingCartViewSet(viewsets.ModelViewSet):
#     serializer_class = ShoppingCartSerializer
#     # permission_classes = (permissions.IsAuthenticated,)
#     # filter_backends = (filters.SearchFilter,)
#     # search_fields = ('user__username', 'recipe__name')

#     def get_queryset(self):
#         new_queryset = self.request.user.shopping_cart.select_related(
#             'user', 'recipe'
#         ).all()
#         return new_queryset
    
#     def perform_create(self, serializer):
#         recipe = get_object_or_404(Recipe, pk=self.kwargs.get('id'))
#         serializer.save(user=self.request.user,
#                         recipe=recipe)
