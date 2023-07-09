import graphene
from graphene_django import DjangoObjectType
from . models import Groceries

class GroceriesType(DjangoObjectType):
    class Meta:
        model = Groceries
        fields = ("lists", "item")



class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hi!")

schema = graphene.Schema(query=Query)
