from django.shortcuts import get_object_or_404

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
                          FavoriteSerializer,
                          IngredientSerializer,
                          RecipeSerializer,
                          # RecipeListRetrieveSerializer,
                          ShoppingCartSerializer,
                          SubscribeSerializer,
                          TagSerializer)

# from .permissions import AuthorOrReadOnly


# class ListCreateDeleteViewSet(mixins.ListModelMixin,
#                               mixins.CreateModelMixin,
#                               mixins.DestroyModelMixin,
#                               viewsets.GenericViewSet):
#     pass

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').all()
    serializer_class = RecipeSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    # pagination_class = pagination.PageNumberPagination
    # filter_backends = (DjangoFilterBackend,)
    # filterset_class = TitleFilterSet

    # def get_serializer_class(self):
    #     if self.action in ['create', 'partial_update']:
    #         return RecipeCreateUpdateSerializer
    #     return RecipeListRetrieveSerializer

    # def update(self, request, *args, **kwargs):
    #     kwargs['partial'] = True
    #     return super().update(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        serializer.save(**self.request.data)

    def perform_create(self, serializer):
        tags = self.request.data['tags']
        serializer.save(tags=tags,
                        author=self.request.user)

    # Не настроено изменение ингредиентов!


class SubscribeViewSet(viewsets.ModelViewSet):
    serializer_class = SubscribeSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ('user__username', 'author__username')
    # http_method_names = ('get', 'post', 'delete')
    # lookup_field = 'subscribe'

    # def get_serializer_class(self):
    #     if self.action == 'list':
    #         return CustomUserSerializer
    #     return super().get_serializer_class()

    def get_queryset(self):
        queryset = self.request.user.subscriptions.select_related(
            'user', 'author'
        ).all()
        return queryset

    def perform_create(self, serializer):
        author = get_object_or_404(CustomUser, pk=self.kwargs.get('id'))
        serializer.save(user=self.request.user,
                        author=author)
        
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


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ('user__username', 'recipe__name')

    # def get_serializer_class(self):
    #     if self.request.method == 'POST':
    #         return RecipeListRetrieveSerializer
    #     return super().get_serializer_class()

    def get_queryset(self):
        new_queryset = self.request.user.favorites.select_related(
            'user', 'recipe'
        ).all()
        return new_queryset

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('id'))
        serializer.save(user=self.request.user,
                        recipe=recipe)
        
        
class ShoppingCartViewSet(viewsets.ModelViewSet):
    serializer_class = ShoppingCartSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ('user__username', 'recipe__name')

    def get_queryset(self):
        new_queryset = self.request.user.shopping_cart.select_related(
            'user', 'recipe'
        ).all()
        return new_queryset
    
    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('id'))
        serializer.save(user=self.request.user,
                        recipe=recipe)
