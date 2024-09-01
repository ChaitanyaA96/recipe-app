"""
Tests for User API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')


def create_user(**kwargs):
    """Create a user and save it to the database"""
    return get_user_model().objects.create_user(**kwargs)


class PublicUserAPITests(TestCase):
    """Test the public user API"""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=None)

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            'email': 'testuser@example.com',
            'password': 'testpass123',
            'name': 'testuser',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_create_user_already_exists(self):
        """Test creating a user that already exists"""
        payload = {
            'email': 'testuser@example.com',
            'password': 'testpass123',
            'name': 'testuser',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password is too short ( 5 characters )"""
        payload = {
            'email': 'testuser@example.com',
            'password': 'pwd',
            'name': 'testuser',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)
