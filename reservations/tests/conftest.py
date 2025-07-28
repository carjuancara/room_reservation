import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.management import call_command


@pytest.fixture(autouse=True)
def setup_test_database(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('flush', '--no-input')


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def make_user(username="testuser", password="testpass", is_staff=False):
        user = User.objects.create_user(
            username=username,
            password=password,
            is_staff=is_staff
        )
        return user
    return make_user


@pytest.fixture
def normal_user(create_user):
    return create_user()


@pytest.fixture
def admin_user(create_user):
    return create_user(username="admin", is_staff=True)


@pytest.fixture
def auth_api_client(api_client, normal_user):
    refresh = RefreshToken.for_user(normal_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def auth_admin_client(api_client, admin_user):
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client
