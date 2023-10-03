from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


def create_relation(request, model, model_relation, pk, serializer, field):
    "Функция создания связи User -> Model."

    model_obj = get_object_or_404(model, pk=pk)
    model_relation_obj = model_relation.objects.filter(
        user=request.user, **{field: model_obj}
    )

    if not model_relation_obj.exists():
        model_relation.objects.create(user=request.user,
                                      **{field: model_obj})
        serializer = serializer(model_obj, context={'request': request})
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)
    return Response(
        data={'errors': 'Попытка повторного добавления объекта'},
        status=status.HTTP_400_BAD_REQUEST
    )


def delete_relation(request, model, model_relation, pk, field):
    "Функция удаления связи User -> Model."

    model_obj = get_object_or_404(model, pk=pk)
    model_relation_obj = model_relation.objects.filter(
        user=request.user, **{field: model_obj}
    )

    if model_relation_obj.exists():
        model_relation_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(
        data={'errors': 'Попытка удаления несуществующего объекта'},
        status=status.HTTP_404_NOT_FOUND
    )


def get_validated_ingredients(ingredients_data, model):
    "Функция валидации ингредиентов рецепта."

    if ingredients_data:
        ingredients_check_list = []
        for ingredient in ingredients_data:
            ingredient_id = ingredient.get('id')
            if ingredient_id in ingredients_check_list:
                raise ValidationError(
                    'Повторное добавление ингредиента в рецепт!'
                )
            amount = ingredient.get('amount')
            if not model.objects.filter(id=ingredient_id).exists():
                raise ValidationError('Несуществующий ингредиент!')
            if not amount or int(amount) < 1:
                raise ValidationError(
                    'Укажите количество используемого ингредиента '
                    '(натуральное число не менее 1)'
                )
            ingredients_check_list.append(ingredient_id)
    else:
        raise ValidationError(
            'Необходимо указать минимум один ингредиент!'
        )

    return ingredients_data


def get_validated_tags(tags_list, model):
    "Функция валидации тегов рецепта."

    if tags_list:
        tags_check_list = []
        for tag_id in tags_list:
            if not model.objects.filter(id=tag_id).exists():
                raise ValidationError('Несуществующий тег!')
            if tag_id in tags_check_list:
                raise ValidationError(
                    'Повторное добавление тега в рецепт!'
                )
            tags_check_list.append(tag_id)
    else:
        raise ValidationError(
            'Необходимо указать минимум один тег!'
        )

    return tags_list
