from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from datetime import date, timedelta
from reservations.models import Clients, Room, Reservation
from reservations.serializers import ClientSerializer, RoomSerializer, ReservationSerializer


class ClientModelTestCase(TestCase):
    """Test cases for Clients model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

    def test_create_client(self):
        """Test creating a client"""
        client = Clients.objects.create(
            user=self.user,
            name='John',
            lastname='Doe',
            document_number='12345678',
            street='123 Main St',
            city='New York',
            state='NY',
            country='USA',
            email='john@example.com',
            phone='+1234567890'
        )
        self.assertEqual(client.name, 'John')
        self.assertEqual(client.user, self.user)
        self.assertEqual(str(client), 'John')

    def test_unique_email_validation(self):
        """Test that email must be unique"""
        Clients.objects.create(
            user=self.user,
            name='John',
            lastname='Doe',
            document_number='12345678',
            street='123 Main St',
            city='New York',
            state='NY',
            country='USA',
            email='john@example.com'
        )

        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='TestPass123!'
        )

        client2 = Clients(
            user=user2,
            name='Jane',
            lastname='Smith',
            document_number='87654321',
            street='456 Oak Ave',
            city='Los Angeles',
            state='CA',
            country='USA',
            email='john@example.com'  # Same email
        )

        with self.assertRaises(ValidationError):
            client2.full_clean()


class RoomModelTestCase(TestCase):
    """Test cases for Room model"""

    def test_create_room(self):
        """Test creating a room"""
        room = Room.objects.create(
            number=101,
            type='single',
            price_for_night=Decimal('100.00'),
            capacity=2,
            description='A cozy single room',
            amenities={
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        )
        self.assertEqual(room.number, 101)
        self.assertEqual(room.type, 'single')
        self.assertEqual(room.price_for_night, Decimal('100.00'))
        self.assertEqual(str(room), 'single')

    def test_room_amenities_validation(self):
        """Test room amenities validation"""
        room = Room(
            number=102,
            type='double',
            price_for_night=Decimal('150.00'),
            capacity=4,
            amenities={'wifi': True}  # Missing required keys
        )

        with self.assertRaises(ValidationError):
            room.full_clean()


class ReservationModelTestCase(TestCase):
    """Test cases for Reservation model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

        self.client = Clients.objects.create(
            user=self.user,
            name='John',
            lastname='Doe',
            document_number='12345678',
            street='123 Main St',
            city='New York',
            state='NY',
            country='USA',
            email='john@example.com'
        )

        self.room = Room.objects.create(
            number=101,
            type='single',
            price_for_night=Decimal('100.00'),
            capacity=2,
            amenities={
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        )

    def test_create_reservation(self):
        """Test creating a reservation"""
        reservation = Reservation.objects.create(
            date_in=date.today() + timedelta(days=1),
            date_out=date.today() + timedelta(days=3),
            number_of_guests=2,
            client=self.client,
            room=self.room
        )

        self.assertEqual(reservation.number_of_guests, 2)
        self.assertEqual(reservation.client, self.client)
        self.assertEqual(reservation.room, self.room)
        self.assertEqual(reservation.total_price,
                         Decimal('200.00'))  # 2 nights * 100

    def test_reservation_date_validation(self):
        """Test that date_out must be after date_in"""
        reservation = Reservation(
            date_in=date.today() + timedelta(days=3),
            date_out=date.today() + timedelta(days=1),  # Before date_in
            number_of_guests=2,
            client=self.client,
            room=self.room
        )

        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_reservation_capacity_validation(self):
        """Test that number of guests cannot exceed room capacity"""
        reservation = Reservation(
            date_in=date.today() + timedelta(days=1),
            date_out=date.today() + timedelta(days=3),
            number_of_guests=5,  # Exceeds room capacity of 2
            client=self.client,
            room=self.room
        )

        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_reservation_overlap_validation(self):
        """Test that overlapping reservations are not allowed"""
        # Create first reservation
        Reservation.objects.create(
            date_in=date.today() + timedelta(days=1),
            date_out=date.today() + timedelta(days=3),
            number_of_guests=2,
            client=self.client,
            room=self.room
        )

        # Try to create overlapping reservation
        reservation2 = Reservation(
            date_in=date.today() + timedelta(days=2),
            date_out=date.today() + timedelta(days=4),
            number_of_guests=1,
            client=self.client,
            room=self.room
        )

        with self.assertRaises(ValidationError):
            reservation2.full_clean()


class ReservationAPITestCase(APITestCase):
    """Test cases for Reservation API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!'
        )

        self.client_obj = Clients.objects.create(
            user=self.user,
            name='John',
            lastname='Doe',
            document_number='12345678',
            street='123 Main St',
            city='New York',
            state='NY',
            country='USA',
            email='john@example.com'
        )

        self.room = Room.objects.create(
            number=101,
            type='single',
            price_for_night=Decimal('100.00'),
            capacity=2,
            amenities={
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        )

        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.user_token = str(refresh.access_token)

        refresh_admin = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh_admin.access_token)

    def test_create_reservation_as_admin(self):
        """Test creating a reservation as admin"""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')

        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 2,
            'client': self.client_obj.id,
            'room': self.room.id
        }

        response = self.client.post('/reservation/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_reservation_as_user_forbidden(self):
        """Test that regular users cannot create reservations"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')

        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 2,
            'client': self.client_obj.id,
            'room': self.room.id
        }

        response = self.client.post('/reservation/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_my_reservations_endpoint(self):
        """Test my reservations endpoint"""
        # Create a reservation for the user
        reservation = Reservation.objects.create(
            date_in=date.today() + timedelta(days=1),
            date_out=date.today() + timedelta(days=3),
            number_of_guests=2,
            client=self.client_obj,
            room=self.room
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')

        response = self.client.get('/reservation/my_reservations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], reservation.id)


class UserRegistrationTestCase(APITestCase):
    """Casos de prueba para el registro de usuarios
    Prueba el registro de usuario con perfil de cliente"""

    def test_user_registration(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'client_profile': {
                'name': 'New',
                'lastname': 'User',
                'document_number': '12345678',
                'street': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'country': 'USA',
                'phone': '+12125551234'  # Formato válido para US
            }
        }

        # Especifica format='json' para datos anidados
        response = self.client.post('/register/', data, format='json')

        # Debug: Imprime la respuesta para ver qué está pasando
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verifica que el usuario fue creado
        user = User.objects.get(username='newuser')
        print(f"User created: {user}")

        # Debug: Verifica cuántos clientes hay en total
        clients_count = Clients.objects.count()
        print(f"Total clients in DB: {clients_count}")

        # Debug: Lista todos los clientes
        all_clients = Clients.objects.all()
        for client in all_clients:
            print(
                f"Client: {client.user.username if client.user else 'No user'} - {client}")

        # Verifica que el perfil del cliente fue creado
        client_exists = Clients.objects.filter(user=user).exists()
        print(f"Client exists for user {user.username}: {client_exists}")

        if not client_exists:
            # Si no existe, intentemos ver si hay algún cliente sin usuario asignado
            orphan_clients = Clients.objects.filter(user__isnull=True)
            print(f"Orphan clients (no user): {orphan_clients.count()}")

        self.assertTrue(
            client_exists, f"Client profile was not created for user {user.username}")

    def test_password_validation(self):
        """Prueba la validación de la contraseña"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'weak',
            'confirm_password': 'weak'
        }

        # También usar format='json' para consistencia
        response = self.client.post('/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_password_mismatch(self):
        """Prueba la falta de coincidencia en la confirmación de la contraseña"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'confirm_password': 'DifferentPass123!'
        }

        # También usar format='json' para consistencia
        response = self.client.post('/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Puedes añadir una aserción específica para el mensaje de error si lo tienes
        # self.assertIn('confirm_password', response.data) # O el campo que indique el error de mismatch
