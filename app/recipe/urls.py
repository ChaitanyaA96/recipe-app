"""
URLs mapping for Recipe
"""
from django.urls import (
    path,
    include,
)
from rest_framework.routers import DefaultRouter
from recipe import views


router = DefaultRouter()
router.register(r'recipes', views.RecipeViewSet)
router.register(r'tags', views.TagViewSet)

router.register(r'ingredients', views.IngredientViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
