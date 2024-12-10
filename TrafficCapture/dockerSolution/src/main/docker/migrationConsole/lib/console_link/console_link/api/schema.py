import graphene
from graphene_django import DjangoObjectType
from typing import List

class Category(graphene.ObjectType):
    name = "name"

    def __str__(self):
        return self.name

class Ingredient(graphene.ObjectType):
    name = "name"
    notes = "Notes"
    category = Category()

    def __str__(self):
        return self.name

class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = ("id", "name", "ingredients")

class IngredientType(DjangoObjectType):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "notes", "category")

class Query(graphene.ObjectType):
    all_ingredients = graphene.List(IngredientType)
    category_by_name = graphene.Field(CategoryType, name=graphene.String(required=True))

    def resolve_all_ingredients(root, info):
        return Ingredient()

    def resolve_category_by_name(root, info, name):
        try:
            return Category(name=name)
        except Category.DoesNotExist:
            return None

schema = graphene.Schema(query=Query)