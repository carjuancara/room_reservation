from rest_framework import serializers
from django.contrib.auth.models import User
from reservations.models import Clients, Room, Reservation

import re


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password',
                  'confirm_password', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True}
        }

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError(
                "Username must be at least 3 characters long.")
        if not value.isalnum():
            raise serializers.ValidationError(
                "Username can only contain letters and numbers.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists.")
        return value

    def validate_password(self, value):
        # Password requirements
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long.")
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter.")
        if not any(char.islower() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one number.")
        if not any(char in '!@#$%^&*()-_=+[]{}|;:,.<>?/' for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one special character.")
        return value

    def validate_email(self, value):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError("Enter a valid email address.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists.")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        # Remove confirm_password before creating user
        validated_data.pop('confirm_password', None)

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class ClientSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(
        source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Clients
        fields = [
            'id',
            'user',
            'name',
            'lastname',
            'document_number',
            'street',
            'city',
            'state',
            'country',
            'email',
            'phone',
            'user_username',
            'user_email',
            'created_at'
        ]
        read_only_fields = ('created_at', 'user')

    def validate_email(self, value):
        if value and Clients.objects.filter(email=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError(
                "A client with this email already exists.")
        return value

    def validate_document_number(self, value):
        if Clients.objects.filter(document_number=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError(
                "A client with this document number already exists.")
        return value


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class ReservationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    client_lastname = serializers.CharField(
        source='client.lastname', read_only=True)
    room_number = serializers.IntegerField(
        source='room.number', read_only=True)
    room_type = serializers.CharField(source='room.type', read_only=True)
    price_per_night = serializers.DecimalField(
        source='room.price_for_night', max_digits=8, decimal_places=2, read_only=True)
    total_nights = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id',
            'date_in',
            'date_out',
            'number_of_guests',
            'status',
            'total_price',
            'client',
            'room',
            'client_name',
            'client_lastname',
            'room_number',
            'room_type',
            'price_per_night',
            'total_nights',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at', 'total_price')

    def get_total_nights(self, obj):
        return (obj.date_out - obj.date_in).days

    def validate(self, data):
        # Validar que la fecha de salida sea posterior a la de entrada
        if data['date_out'] <= data['date_in']:
            raise serializers.ValidationError(
                "The departure date must be after the arrival date."
            )

        # Validar número de huéspedes
        if data.get('number_of_guests', 1) <= 0:
            raise serializers.ValidationError(
                "The number of guests must be at least 1."
            )

        # Validar capacidad de la habitación
        room = data.get('room')
        if room and room.capacity < data.get('number_of_guests', 1):
            raise serializers.ValidationError(
                f"The room capacity is {room.capacity}, but you requested {data.get('number_of_guests', 1)} guests."
            )

        # Validar disponibilidad de la habitación
        if room:
            overlapping_reservations = Reservation.objects.filter(
                room=room,
                date_in__lt=data['date_out'],
                date_out__gt=data['date_in'],
                status__in=['pending', 'confirmed']
            )

            # Excluir la reservación actual si estamos actualizando
            if self.instance:
                overlapping_reservations = overlapping_reservations.exclude(
                    id=self.instance.id)

            if overlapping_reservations.exists():
                raise serializers.ValidationError(
                    "The room is not available for the selected dates."
                )

            # Verificar estado de la habitación
            if room.status not in ['available']:
                raise serializers.ValidationError(
                    f"The room is not available due to its current status: {room.get_status_display()}"
                )

        return data

    def create(self, validated_data):
        # El precio total se calculará automáticamente en el método save del modelo
        return super().create(validated_data)
