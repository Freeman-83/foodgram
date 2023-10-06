from django.contrib import admin

from .models import (Favorite,
                     Ingredient,
                     IngredientRecipe,
                     Recipe,
                     Tag,
                     TagRecipe,
                     ShoppingCart,
                     Subscribe)


class IngredientInRecipe(admin.TabularInline):
    model = IngredientRecipe
    min_num = 1


class TagInRecipe(admin.TabularInline):
    model = TagRecipe
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'additions_in_favorite_count')
    list_display_links = ('name',)
    readonly_fields = ('additions_in_favorite_count',)
    search_fields = ('author', 'name')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'

    inlines = [IngredientInRecipe, TagInRecipe]

    @admin.display(description='Количество добавлений в избранное')
    def additions_in_favorite_count(self, recipe):
        return recipe.in_favorite_for_users.all().count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'color')
    list_filter = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'ingredient', 'recipe')
    list_filter = ('ingredient',)


@admin.register(TagRecipe)
class TagRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag', 'recipe')
    list_filter = ('tag',)


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_filter = ('user',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user',)
