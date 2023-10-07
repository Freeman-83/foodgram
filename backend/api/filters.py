from django_filters.rest_framework import (FilterSet,
                                           BooleanFilter,
                                           CharFilter,
                                           ModelMultipleChoiceFilter)

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilterSet(FilterSet):

    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilterSet(FilterSet):

    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    is_favorited = BooleanFilter(
        field_name='in_favorite_for_users',
        method='is_exist_filter'
    )

    is_in_shopping_cart = BooleanFilter(
        field_name='in_shopping_cart_for_users',
        method='is_exist_filter'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def is_exist_filter(self, queryset, name, value):
        lookup = '__'.join([name, 'user'])
        if self.request.user.is_anonymous:
            return queryset
        return queryset.filter(**{lookup: self.request.user})
