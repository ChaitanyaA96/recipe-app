"""
Tests for Recipe API
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **kwargs):
    """Create a new recipe"""
    defaults = {
        'title': 'Test Recipe',
        'time_minutes': 10,
        'price': Decimal(10),
        'description': 'Test Recipe description',
        'link': 'http://test.com',
    }

    defaults.update(kwargs)

    return Recipe.objects.create(user=user, **defaults)


def create_user(**kwargs):
    """Create a new user"""
    return get_user_model().objects.create_user(**kwargs)


class PublicRecipeApiTests(TestCase):
    """Test the Public Recipe API Unauthenticated"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving recipes"""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test the Private/Authenticated Recipe API"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='test123')
        self.user = get_user_model().objects.create_user(
            'testuser@example.com',
            'testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for authenticated user"""
        user2 = create_user(
            email='testuser2@example.com',
            password='testpass123'
        )
        create_recipe(user2)
        create_recipe(user=self.user)
        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test retrieving a recipe detail"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a new recipe"""
        payload = {
            'title': 'Test Recipe',
            'time_minutes': 10,
            'price': Decimal(10),
            'description': 'Test Recipe description',
            'link': 'http://test.com',
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title='Test Recipe',
            link=original_link,
        )

        payload = {'title': 'New Test Recipe'}
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """Test full update recipe"""
        recipe = create_recipe(
            user=self.user,
            title='Test Recipe',
            link='http://test.com/recipe.pdf',
            description='Test Recipe description',
        )

        payload = {
            'title': 'New Test Recipe',
            'link': 'http://newtest.com/recipe.pdf',
            'description': 'New Test Recipe description',
            'time_minutes': 10,
            'price': Decimal(10),
        }

        url = detail_url(recipe.id)
        response = self.client.put(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test updating a user returns error"""
        new_user = create_user(email='newuser@example.com', password='test123')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        """Test trying to delete other user's recipe gives error"""
        new_user = create_user(email='newuser@example.com', password='test123')
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a new recipe with tags"""
        payload = {
            'title': 'Test Recipe',
            'time_minutes': 10,
            'price': Decimal(10),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        self.assertEqual(recipe[0].tags.count(), 2)
        for tag in payload['tags']:
            exits = recipe[0].tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exits)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a new recipe with existing tags"""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Test Recipe',
            'time_minutes': 10,
            'price': Decimal(10),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        self.assertEqual(recipe[0].tags.count(), 2)
        self.assertIn(tag_indian, recipe[0].tags.all())
        for tag in payload['tags']:
            exits = recipe[0].tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exits)

    def test_create_tag_on_update(self):
        """Test creating a new tag on updating a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {
            'tags': [{'name': 'Lunch'}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tags(self):
        """Test assigning existing tags to a recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {
            'tags': [{'name': 'Lunch'}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing existing tags on a recipe"""
        recipe = create_recipe(user=self.user)
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe.tags.add(tag)

        payload = {'tags': [], }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredient(self):
        """Test creating a new recipe with new ingredients"""
        payload = {
            'title': 'Test Recipe',
            'time_minutes': 10,
            'price': Decimal(10),
            'ingredients': [{'name': 'Cauliflower'}, {'name': 'salt'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        self.assertEqual(recipe[0].ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exits = recipe[0].ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exits)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new recipe with existing ingredients"""
        ingredient = Ingredient.objects.create(user=self.user, name='Lemon')
        payload = {
            'title': 'Test Recipe',
            'time_minutes': 10,
            'price': Decimal(10),
            'ingredients': [{'name': 'Lemon'}, {'name': 'fish'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        self.assertEqual(recipe[0].ingredients.count(), 2)
        self.assertIn(ingredient, recipe[0].ingredients.all())
        for ingredient in payload['ingredients']:
            exits = recipe[0].ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exits)

    def test_create_ingredient_on_update(self):
        """Test creating a new ingredient on updating a recipe"""
        recipe = create_recipe(user=self.user)
        payload = {'ingredients': [{'name': 'Cauliflower'}, ]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(
            user=self.user,
            name='Cauliflower'
        )
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning existing ingredients to a recipe"""
        recipe = create_recipe(user=self.user)
        ingredient = Ingredient.objects.create(user=self.user, name='Lemon')
        recipe.ingredients.add(ingredient)

        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name='Cauliflower'
        )
        payload = {
            'ingredients': [{'name': 'Cauliflower'}, ],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing existing ingredients on a recipe"""
        recipe = create_recipe(user=self.user)
        ingredient = Ingredient.objects.create(user=self.user, name='Lemon')
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': [], }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
