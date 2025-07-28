from reservations.models import Clients, Reservation, Room
from django.core.exceptions import ValidationError
from datetime import datetime, date
from decimal import Decimal

import pytest


@pytest.fixture
def new_client():
    # Crear un usuario en la base de datos de prueba
    return Clients.objects.create(
        name="Juan Ignacio",
        lastname="Perez",
        document_number="d5846795122",
        street="España 246",
        city="Barcelona",
        state="Barcelona",
        country="España",
        email="juanignacio@email.com",
        phone="+30382145897",
    )


@pytest.mark.django_db
class TestClients:
    def test_create_client(self, new_client):
        """
        Verificar que el usuario se creó correctamente
        """

        assert Clients.objects.count() == 1

    def test_verify_client_data(self, new_client):
        """
        Verificar que el cliente tiene datos con longitudes válidas
        """
        client = Clients.objects.get(id=new_client.id)

        # Diccionario de campos y sus longitudes máximas
        field_lengths = {
            "name": 50,
            "lastname": 50,
            "document_number": 15,
            "street": 100,
            "city": 50,
            "state": 50,
            "country": 50,
        }

        for field, max_length in field_lengths.items():
            value = getattr(client, field)
        assert len(value) <= max_length, f"El campo '{
            field}' excede la longitud máxima de {max_length}"

    def test_verify_type_data(self, new_client):
        """
        verifica que los datos son del tipo correcto
        """

        client = Clients.objects.get(id=new_client.id)
        assert type(client.name) is str
        assert type(client.lastname) is str
        assert type(client.document_number) is str
        assert type(client.street) is str
        assert type(client.city) is str
        assert type(client.state) is str
        assert type(client.country) is str

    def test_email_must_be_unique(self, new_client):
        """
        Verifica que el correo electrónico no esté repetido
        """
        # Crear un nuevo cliente con el mismo email que el cliente existente
        duplicate_client = Clients(
            name="Juan",
            lastname="Perez",
            email=new_client.email,  # Mismo email que el cliente existente
            phone="+30382145897"
        )

        # Se espera que la validación falle debido a la restricción de unicidad
        with pytest.raises(ValidationError, match="El email debe ser único."):
            duplicate_client.full_clean()

    def test_minimum_fields(self, new_client):
        """
        Verifica que los campos obligatorios tengan valores no vacíos
        """
        # Lista de campos obligatorios
        MINIMUM_FIELDS = [
            "name",
            "lastname",
            "document_number",
            "street",
            "city",
            "state",
            "country",
            "email"
        ]

        # Verificar que cada campo obligatorio tiene un valor no vacío
        for field in MINIMUM_FIELDS:
            # Obtener el valor del campo
            value = getattr(new_client, field, None)
            assert value, f"El campo '{
                field}' está vacío o no tiene un valor válido"

    def test_client_reservation_relation(self):
        # Creamos un cliente
        client = Clients.objects.create(
            name="Juan",
            lastname="Perez",
            email="juan.perez@example.com",
            document_number="1234567890",
            street="Calle Falsa 123",
            city="Madrid",
            state="Madrid",
            country="España",
            phone="+34600123456"
        )

        # creamos una habitacion para los test
        room = Room.objects.create(
            number=1,
            type='single',
            price_for_night=Decimal('100.00'),
            is_reserved=False,
            status='available',
            description='descripcion de la habitacion',
            capacity=4,
            amenities={'wifi': True, 'air_conditioning': True, 'minibar': False,
                       'jacuzzi': False, 'tv': True, 'breakfast_included': True}

        )

        # Creamos una reserva para ese cliente
        reservation = Reservation.objects.create(
            date_in=date(2025, 1, 1),
            date_out=date(2025, 1, 5),
            number_of_guests=2,
            status="pending",
            client=client,  # Relación con el cliente
            room=room,  # Usar la instancia room creada arriba
        )

        # Verificamos que la reserva está asociada correctamente con el cliente
        # La relación debe ser la misma instancia de cliente
        assert reservation.client == client

        # También podemos verificar que el cliente tiene reservas asociadas
        # Usamos el related_name 'reservations' para acceder a las reservas del cliente
        assert reservation in client.reservations.all()

        # Aseguramos que los datos de la reserva son correctos
        assert reservation.date_in == date(2025, 1, 1)
        assert reservation.date_out == date(2025, 1, 5)
        assert reservation.status == "pending"
        assert reservation.number_of_guests == 2
        # El precio total se calcula automáticamente: 4 noches * 100.00 = 400.00
        assert reservation.total_price == Decimal('400.00')
