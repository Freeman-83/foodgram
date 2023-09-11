from django.urls import include, path

from rest_framework import routers

from .views import (IngredientViewSet,
                    RecipeViewSet,
                    SubscribeViewSet,
                    TagViewSet)

app_name = 'api'

router = routers.DefaultRouter()

router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('users/subscriptions',
                SubscribeViewSet,
                basename='subscriptions')
router.register('users/(?P<id>\d+)/subscribe',
                SubscribeViewSet,
                basename='subscribe')

# router.register('recipes/<int:pk>/favorite/',
#                 FavoriteViewSet,
#                 basename='favorite')
# router.register('recipes/<int:pk>/shopping_cart/',
#                 ShoppingCartViewSet,
#                 basename='shopping_cart')
# router.register('recipes/<int:pk>/download_shopping_cart/',
#                 ShoppingCartViewSet,
#                 basename='download_shopping_cart')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
