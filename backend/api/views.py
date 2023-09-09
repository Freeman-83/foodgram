from django.shortcuts import get_object_or_404

from rest_framework import filters, mixins, pagination, permissions, viewsets

from recipes.models import (Favorite,
                            Ingredient,
                            Recipe,
                            ShoppingCart,
                            Subscribe,
                            Tag)

from user.models import CustomUser

from .serializers import (IngredientSerializer,
                          RecipeListRetrieveSerializer,
                          RecipeCreateUpdateSerializer,
                          TagSerializer)

# from .permissions import AuthorOrReadOnly


# class ListRetrieveViewSet(mixins.ListModelMixin,
#                           mixins.RetrieveModelMixin,
#                           viewsets.GenericViewSet):
#     pass

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
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


# class FavoriteViewSet(viewsets.ModelViewSet):
#     serializer_class = FavoriteSerializer
#     # permission_classes = (permissions.IsAuthenticated,)
#     # filter_backends = (filters.SearchFilter,)
#     search_fields = ('user__username', 'following__username')

#     def get_queryset(self):
#         new_queryset = self.request.user.follower.select_related(
#             'user', 'following'
#         ).all()
#         return new_queryset

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)


# class FollowViewSet(ListCreateViewSet):
#     serializer_class = FollowSerializer
#     permission_classes = (permissions.IsAuthenticated,)
#     filter_backends = (filters.SearchFilter,)
#     search_fields = ('user__username', 'following__username')

#     def get_queryset(self):
#         new_queryset = self.request.user.follower.select_related(
#             'user', 'following'
#         ).all()
#         return new_queryset

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)