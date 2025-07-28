import pytest
from reservations.models import Reservation, Clients, Room
from datetime import datetime, date
from decimal import Decimal
from django.core.exceptions import ValidationError


@pytest.fixture
def new_reservation():
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
        room=room,  # Usar la instancia room directamente
    )

    return reservation


@pytest.mark.django_db
class TestReservation:
    def test_create_reservation(self, new_reservation):
        assert Reservation.objects.count() == 1

    def test_verify_data_with_valid_length(self, new_reservation):
        """
        Verificar que la RESERVACION tiene datos con longitudes válidas
        """
        reservation = Reservation.objects.get(id=new_reservation.id)

        # Diccionario de campos y sus longitudes máximas
        field_lengths = {
            "status": 9,
        }

        for field, max_length in field_lengths.items():
            value = getattr(reservation, field)
        assert len(value) <= max_length, f"El campo '{
            field}' excede la longitud máxima de {max_length}"

    def test_verify_type_data(self, new_reservation):
        """
        verifica que los datos son del tipo correcto
        """

        reservation = Reservation.objects.get(id=new_reservation.id)
        assert type(reservation.date_in) is date
        assert type(reservation.date_out) is date
        assert type(reservation.status) is str
        assert type(reservation.total_price) is Decimal
        assert type(reservation.created_at) is date
        assert type(reservation.updated_at) is date

    def test_minimum_fields(self, new_reservation):
        """
        Verifica que los campos obligatorios tengan valores no vacíos
        """
        # Lista de campos obligatorios
        MINIMUM_FIELDS = [
            "date_in",
            "date_out",
            "status",
            "total_price",
            "created_at",
            "updated_at",
            "client",
            "room",
        ]

        # Verificar que cada campo obligatorio tiene un valor no vacío
        for field in MINIMUM_FIELDS:
            # Obtener el valor del campo
            value = getattr(new_reservation, field)
            assert value, f"El campo '{
                field}' está vacío o no tiene un valor válido"
