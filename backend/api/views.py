from django.shortcuts import get_object_or_404

from rest_framework import status
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
                          FavoriteSerializer,
                          IngredientSerializer,
                          RecipeCreateUpdateSerializer,
                          RecipeListRetrieveSerializer,
                          SubscribeSerializer,
                          TagSerializer)

# from .permissions import AuthorOrReadOnly


class ListCreateDeleteViewSet(mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              mixins.DestroyModelMixin,
                              viewsets.GenericViewSet):
    pass

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').all()

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return RecipeCreateUpdateSerializer
        return RecipeListRetrieveSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class SubscribeViewSet(ListCreateDeleteViewSet):
    serializer_class = SubscribeSerializer
    # queryset = Subscribe.objects.all()
    # permission_classes = (permissions.IsAuthenticated,)
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ('user__username', 'author__username')

    # def get_serializer_class(self):
    #     if self.action == 'list':
    #         return CustomUserSerializer
    #     return super().get_serializer_class()

    def get_queryset(self):
        queryset = self.request.user.subscriptions.select_related(
            'author', 'user'
        ).all()
        return queryset

    def perform_create(self, serializer):
        author = get_object_or_404(CustomUser, pk=self.kwargs.get('id'))
        serializer.save(user=self.request.user,
                        author=author,
                        is_subscribed=True)
        
    # Не настроено удаление


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ('user__username', 'following__username')

    def get_queryset(self):
        new_queryset = self.request.user.favorites.select_related(
            'user', 'favorites'
        ).all()
        return new_queryset
    
    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('id'))
        serializer.save(user=self.request.user,
                        recipe=recipe,
                        is_favorite=True)
