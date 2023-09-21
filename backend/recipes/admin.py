from django.contrib import admin
from django.contrib.admin import display

from .models import (Favorite,
                     Ingredient,
                     IngredientRecipe,
                     Recipe,
                     Tag,
                     TagRecipe,
                     ShoppingCart,
                     Subscribe)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author')
    readonly_fields = ('additions_in_favorite_count',)
    search_fields = ('author', 'name')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'

    @display(description='Количество добавлений в избранное')
    def additions_in_favorite_count(self, recipe):
        return recipe.in_favorite_for_users.all().count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'color')
    list_filter = ('name',)


class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'ingredient', 'recipe')
    list_filter = ('ingredient',)


class TagRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag', 'recipe')
    list_filter = ('tag',)


class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_filter = ('user',)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user',)


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user',)


admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientRecipe, IngredientRecipeAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(TagRecipe, TagRecipeAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Subscribe, SubscribeAdmin)
