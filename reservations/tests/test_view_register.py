import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


class TestRegisterUser:
    def test_register_user_success(self, api_client):
        url = reverse('reservations:register-list')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'P@ssw0rd123',
            'confirm_password': 'P@ssw0rd123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='testuser').exists()

    def test_register_user_missing_fields(self, api_client):
        url = reverse('reservations:register-list')
        data = {
            'username': 'testuser',
            'password': 'P@ssw0rd123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data or 'confirm_password' in response.data

    def test_register_user_invalid_email(self, api_client):
        url = reverse('reservations:register-list')
        data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'P@ssw0rd123',
            'confirm_password': 'P@ssw0rd123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_register_user_duplicate_username(self, api_client):
        # Create first user
        url = reverse('reservations:register-list')
        data = {
            'username': 'testuser1',
            'email': 'testuser1@example.com',
            'password': 'P@ssw0rd123',
            'confirm_password': 'P@ssw0rd123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

        # Try to create user with same username
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data

    def test_register_user_duplicate_email(self, api_client):
        # Create first user
        url = reverse('reservations:register-list')
        data = {
            'username': 'testuser1',
            'email': 'testuser@example.com',
            'password': 'P@ssw0rd123',
            'confirm_password': 'P@ssw0rd123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

        # Try to create user with same email
        data['username'] = 'testuser2'
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_register_user_weak_password_too_short(self, api_client):
        url = reverse('reservations:register-list')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': '123',  # Too short password
            'confirm_password': '123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_register_user_weak_password_no_uppercase(self, api_client):
        url = reverse('reservations:register-list')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123',  # No uppercase letter
            'confirm_password': 'password123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_register_user_weak_password_no_numbers(self, api_client):
        url = reverse('reservations:register-list')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'Password',  # No numbers
            'confirm_password': 'Password'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_register_user_weak_password_no_special_characters(self, api_client):
        url = reverse('reservations:register-list')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'Password123',  # No special characters
            'confirm_password': 'Password123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_register_user_password_mismatch(self, api_client):
        url = reverse('reservations:register-list')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'P@ssw0rd123',
            'confirm_password': 'DifferentP@ss123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data or 'confirm_password' in response.data
