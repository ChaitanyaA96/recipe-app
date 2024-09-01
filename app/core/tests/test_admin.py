"""
Test for Django admin modification
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client


class AdminTestCase(TestCase):
    """Tests for Django admin"""

    def setUp(self):
        """Create User and Client for testing"""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='testpass123',
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='testpass123',
            name='Test User',
        )

    def test_users_list(self):
        """Test users listed on page"""
        url = reverse('admin:core_user_changelist')
        response = self.client.get(url)

        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.email)

    def test_user_edit_page(self):
        """Test user edit page"""
        url = reverse('admin:core_user_change', args=(self.user.id,))
        response = self.client.get(url)

        self.assertEquals(response.status_code, 200)

    def test_create_user_page(self):
        """Test user create page"""
        url = reverse('admin:core_user_add')
        response = self.client.get(url)

        self.assertEquals(response.status_code, 200)
