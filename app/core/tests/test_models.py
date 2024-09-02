"""
Tests for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from core import models


def create_user(email='user@example.com', password='testuser123'):
    """Create and return new user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test Models"""

    def test_create_users_with_email_successful(self):
        """Test creating a new user with email is successful"""
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email, password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        sample_emails = [
            ['test1@Example.com', 'test1@example.com'],
            ['Test2@EXAMPLE.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test creating a new user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'sample1223')

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'testpass123',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a recipe"""
        user = get_user_model().objects.create_user(
            'receipetest@example.com',
            'testpass123',
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample recipe name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='This is a sample recipe description',
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test creating a tag"""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='tag1')
        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test creating an ingredient"""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Ingredient 1'
        )
        self.assertEqual(str(ingredient), ingredient.name)
