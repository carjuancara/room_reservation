import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from reservations.models import Clients, Room, Reservation
from django.contrib.auth.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    """Fixture para instancia de APIClient"""
    return APIClient()


@pytest.fixture
def test_user():
    """Fixture para crear un usuario de prueba"""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='TestPass123!'
    )


@pytest.fixture
def new_client(db):
    """Fixture para crear un usuario"""
    return {
        "name": "testuser",
        "lastname": "test lastuser",
        "email": "test@example.com",
        "document_number": "545874580",
        "street": "san miguel 123",
        "city": "lules",
        "state": "state_street",
        "country": "country1"}


class TestClientView:
    def test_create_client(self, api_client, test_user, new_client):
        api_client.force_authenticate(user=test_user)
        api_url = reverse('reservations:client-list')
        response = api_client.post(api_url, new_client, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Clients.objects.filter(user=test_user).exists()

    def test_admin_can_list_all_clients(self, api_client):
        # Create admin user
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!'
        )

        # Create regular user with client profile
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='RegularPass123!'
        )

        Clients.objects.create(
            user=regular_user,
            name='Regular',
            lastname='User',
            document_number='12345678',
            email='regular@example.com'
        )

        # Admin can see all clients
        api_client.force_authenticate(user=admin_user)
        api_url = reverse('reservations:client-list')
        response = api_client.get(api_url, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

    def test_create_client_without_authentication(self, api_client, new_client):
        api_url = reverse('reservations:client-list')
        response = api_client.post(api_url, new_client, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
