import pytest
from django.contrib.auth.models import User
from reservations.models import Clients, Room, Reservation
from datetime import date
from decimal import Decimal

from reservations.serializers import (
    UserSerializer,
    ClientSerializer,
    RoomSerializer,
    ReservationSerializer
)

pytestmark = pytest.mark.django_db


class TestUserSerializer:
    def test_create_user_success(self):
        """Test successful user creation"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'confirm_password': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

        serializer = UserSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.check_password('TestPass123!')

    def test_password_validation_too_short(self):
        """Test password validation - too short"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123',
            'confirm_password': '123'
        }

        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
        assert 'at least 8 characters' in str(serializer.errors['password'])

    def test_password_validation_no_uppercase(self):
        """Test password validation - no uppercase"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123!',
            'confirm_password': 'password123!'
        }

        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
        assert 'uppercase letter' in str(serializer.errors['password'])

    def test_password_validation_no_lowercase(self):
        """Test password validation - no lowercase"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'PASSWORD123!',
            'confirm_password': 'PASSWORD123!'
        }

        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
        assert 'lowercase letter' in str(serializer.errors['password'])

    def test_password_validation_no_numbers(self):
        """Test password validation - no numbers"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password!',
            'confirm_password': 'Password!'
        }

        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
        assert 'number' in str(serializer.errors['password'])

    def test_password_validation_no_special_chars(self):
        """Test password validation - no special characters"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }

        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
        assert 'special character' in str(serializer.errors['password'])

    def test_username_validation_too_short(self):
        """Test username validation - too short"""
        data = {
            'username': 'ab',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'confirm_password': 'TestPass123!'
        }

        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'username' in serializer.errors
        assert 'at least 3 characters' in str(serializer.errors['username'])

    def test_username_validation_non_alphanumeric(self):
        """Test username validation - non-alphanumeric characters"""
        data = {
            'username': 'test@user',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'confirm_password': 'TestPass123!'
        }

        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'username' in serializer.errors
        assert 'letters and numbers' in str(serializer.errors['username'])

    def test_username_validation_duplicate(self):
        """Test username validation - duplicate username"""
        User.objects.create_user(username='existing', email='existing@example.com')

        data = {
            'username': 'existing',
            'email': 'new@example.com',
            'password': 'TestPass123!',
            'confirm_password': 'TestPass123!'
        }

        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'username' in serializer.errors
        assert 'already exists' in str(serializer.errors['username'])

    def test_email_validation_invalid_format(self):
        """Test email validation - invalid format"""
        data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'TestPass123!',
            'confirm_password': 'TestPass123!'
        }

        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
        assert 'valid email address' in str(serializer.errors['email'])

    def test_email_validation_duplicate(self):
        """Test email validation - duplicate email"""
        User.objects.create_user(username='existing', email='existing@example.com')

        data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'TestPass123!',
            'confirm_password': 'TestPass123!'
        }

        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
        assert 'already exists' in str(serializer.errors['email'])

    def test_password_confirmation_mismatch(self):
        """Test password confirmation mismatch"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'confirm_password': 'DifferentPass123!'
        }

        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'not match' in str(serializer.errors['non_field_errors'])


class TestClientSerializer:
    @pytest.fixture
    def test_user(self):
        return User.objects.create_user(
            username='John',
            email='john@example.com'
        )

    def test_create_client_success(self, test_user):
         """Test successful client creation"""
         data = {
             'user': test_user.id,
             'name': 'John',
             'lastname': 'Doe',
             'document_number': '12345678',
             'street': '123 Main St',
             'city': 'New York',
             'state': 'NY',
             'country': 'USA',
             'email': 'john@example.com',

         }

         serializer = ClientSerializer(data=data)

         # Debug: mostrar errores si no es válido
         if not serializer.is_valid():
             print("Errores del serializer:", serializer.errors)

         # Verificar que el serializer es válido
         assert serializer.is_valid(), f"Serializer validation failed: {serializer.errors}"

         # Guardar el cliente
         client = serializer.save()

         # Verificar los datos del cliente creado
         assert client.name == 'John'
         assert client.lastname == 'Doe'
         assert client.document_number == '12345678'
         assert client.street == '123 Main St'
         assert client.city == 'New York'
         assert client.state == 'NY'
         assert client.country == 'USA'
         assert client.email == 'john@example.com'


    def test_email_uniqueness_validation(self, test_user):
        """Test email uniqueness validation"""
        # Create existing client
        Clients.objects.create(
            user=test_user,
            name='Existing',
            lastname='User',
            document_number='11111111',
            email='existing@example.com'
        )

        # Try to create new client with same email
        data = {
            'name': 'New',
            'lastname': 'User',
            'document_number': '22222222',
            'email': 'existing@example.com'
        }

        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
        assert 'already exists' in str(serializer.errors['email'])

    def test_document_number_uniqueness_validation(self, test_user):
        """Test document number uniqueness validation"""
        # Create existing client
        Clients.objects.create(
            user=test_user,
            name='Existing',
            lastname='User',
            document_number='12345678',
            email='existing@example.com'
        )

        # Try to create new client with same document number
        data = {
            'name': 'New',
            'lastname': 'User',
            'document_number': '12345678',
            'email': 'new@example.com'
        }

        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert 'document_number' in serializer.errors
        assert 'already exists' in str(serializer.errors['document_number'])



class TestRoomSerializer:
    def test_create_room_success(self):
        """Test successful room creation"""
        data = {
            'number': 101,
            'type': 'single',
            'price_for_night': '150.00',
            'status': 'available',
            'capacity': 2,
            'description': 'A nice room',
            'amenities': {
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        }

        serializer = RoomSerializer(data=data)
        assert serializer.is_valid()

        room = serializer.save()
        assert room.number == 101
        assert room.type == 'single'
        assert room.price_for_night == Decimal('150.00')
        assert room.capacity == 2

    def test_invalid_room_type(self):
        """Test invalid room type validation"""
        data = {
            'number': 101,
            'type': 'invalid_type',
            'price_for_night': '150.00',
            'status': 'available',
            'capacity': 2,
            'amenities': {
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        }

        serializer = RoomSerializer(data=data)
        assert not serializer.is_valid()
        assert 'type' in serializer.errors

    def test_invalid_status(self):
        """Test invalid status validation"""
        data = {
            'number': 101,
            'type': 'single',
            'price_for_night': '150.00',
            'status': 'invalid_status',
            'capacity': 2,
            'amenities': {
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        }

        serializer = RoomSerializer(data=data)
        assert not serializer.is_valid()
        assert 'status' in serializer.errors

    def test_invalid_amenities_missing_keys(self):
        """Test amenities validation with missing required keys"""
        data = {
            'number': 101,
            'type': 'single',
            'price_for_night': '150.00',
            'status': 'available',
            'capacity': 2,
            'amenities': {
                'wifi': True,
                'air_conditioning': True
                # Missing other required keys
            }
        }

        serializer = RoomSerializer(data=data)
        assert not serializer.is_valid()
        assert 'amenities' in serializer.errors


class TestReservationSerializer:
    @pytest.fixture
    def test_user(self):
        return User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )

    @pytest.fixture
    def test_client(self, test_user):
        return Clients.objects.create(
            user=test_user,
            name='John',
            lastname='Doe',
            document_number='12345678',
            email='john@example.com'
        )

    @pytest.fixture
    def test_room(self):
        return Room.objects.create(
            number=101,
            type='double',
            price_for_night=Decimal('150.00'),
            status='available',
            capacity=2,
            amenities={
                'wifi': True,
                'air_conditioning': True,
                'minibar': True,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        )

    def test_create_reservation_success(self, test_client, test_room):
        """Test successful reservation creation"""
        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 2,
            'client': test_client.id,
            'room': test_room.id
        }

        serializer = ReservationSerializer(data=data)
        assert serializer.is_valid()

        reservation = serializer.save()
        assert reservation.date_in == date(2024, 12, 25)
        assert reservation.date_out == date(2024, 12, 27)
        assert reservation.number_of_guests == 2
        assert reservation.total_price == Decimal('300.00')  # 2 nights * 150

    def test_invalid_date_range(self, test_client, test_room):
        """Test invalid date range validation"""
        data = {
            'date_in': '2024-12-27',
            'date_out': '2024-12-25',  # Before date_in
            'number_of_guests': 2,
            'client': test_client.id,
            'room': test_room.id
        }

        serializer = ReservationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'after the arrival date' in str(serializer.errors['non_field_errors'])

    def test_invalid_guest_number_zero(self, test_client, test_room):
        """Test invalid guest number validation - zero guests"""
        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 0,
            'client': test_client.id,
            'room': test_room.id
        }

        serializer = ReservationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'at least 1' in str(serializer.errors['non_field_errors'])

    def test_exceeds_room_capacity(self, test_client, test_room):
        """Test guest number exceeds room capacity"""
        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 5,  # Room capacity is 2
            'client': test_client.id,
            'room': test_room.id
        }

        serializer = ReservationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'capacity' in str(serializer.errors['non_field_errors'])

    def test_room_not_available_status(self, test_client):
        """Test room not available due to status"""
        maintenance_room = Room.objects.create(
            number=102,
            type='single',
            price_for_night=Decimal('100.00'),
            status='maintenance',
            capacity=1,
            amenities={
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        )

        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 1,
            'client': test_client.id,
            'room': maintenance_room.id
        }

        serializer = ReservationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'current status' in str(serializer.errors['non_field_errors'])

    def test_overlapping_reservation(self, test_client, test_room):
        """Test overlapping reservation validation"""
        # Create existing reservation
        Reservation.objects.create(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=1,
            status='confirmed',
            client=test_client,
            room=test_room
        )

        # Try to create overlapping reservation
        data = {
            'date_in': '2024-12-26',
            'date_out': '2024-12-28',
            'number_of_guests': 1,
            'client': test_client.id,
            'room': test_room.id
        }

        serializer = ReservationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'not available for the selected dates' in str(serializer.errors['non_field_errors'])

    def test_readonly_fields(self, test_client, test_room):
        """Test readonly fields are not updated"""
        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 2,
            'client': test_client.id,
            'room': test_room.id,
            'total_price': '999.99',  # Should be ignored
            'created_at': '2020-01-01',  # Should be ignored
            'updated_at': '2020-01-01'   # Should be ignored
        }

        serializer = ReservationSerializer(data=data)
        assert serializer.is_valid()

    def test_serializer_method_fields(self, test_client, test_room):
        """Test calculated and related fields in serializer"""
        reservation = Reservation.objects.create(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=2,
            client=test_client,
            room=test_room
        )

        serializer = ReservationSerializer(reservation)
        data = serializer.data

        assert data['client_name'] == 'John'
        assert data['client_lastname'] == 'Doe'
        assert data['room_number'] == 101
        assert data['room_type'] == 'double'
        assert float(data['price_per_night']) == 150.00
        assert data['total_nights'] == 2

    def test_cancelled_reservation_doesnt_block(self, test_client, test_room):
        """Test that cancelled reservations don't block new ones"""
        # Create cancelled reservation
        Reservation.objects.create(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=1,
            status='cancelled',
            client=test_client,
            room=test_room
        )

        # Should be able to create new reservation for same dates
        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 2,
            'client': test_client.id,
            'room': test_room.id
        }

        serializer = ReservationSerializer(data=data)
        assert serializer.is_valid()
