from django.contrib import admin

from .models import (Favorite,
                     Ingredient,
                     IngredientRecipe,
                     Recipe,
                     Tag,
                     TagRecipe,
                     ShoppingCart,
                     Subscribe)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'name', 'text', 'cooking_time', 'image')
    search_fields = ('author', 'name')
    list_filter = ('author', 'name', 'tags')
    # list_editable = ('text',)
    empty_value_display = '-пусто-'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'ingredient', 'recipe')
    list_filter = ('ingredient',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'color')
    list_filter = ('name',)


class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_filter = ('user',)


admin.site.register(Favorite)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientRecipe, IngredientRecipeAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(TagRecipe)
admin.site.register(ShoppingCart)
admin.site.register(Subscribe, SubscribeAdmin)
