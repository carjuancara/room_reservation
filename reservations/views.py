from rest_framework import viewsets, status
from django.contrib.auth.models import User
from reservations.models import Clients, Room, Reservation
from reservations.serializers import ClientSerializer, RoomSerializer, ReservationSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError

from datetime import datetime, date
import re


class RegisterUser(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Validate email format
        email = request.data.get('email')
        if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return Response({"email": ["Enter a valid email address."]}, status=status.HTTP_400_BAD_REQUEST)

        # Validate password
        password = request.data.get('password')
        if not password:
            return Response({"password": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        # Password requirements
        if len(password) < 8:
            return Response({"password": ["Password must be at least 8 characters long."]}, status=status.HTTP_400_BAD_REQUEST)
        if not any(char.isupper() for char in password):
            return Response({"password": ["Password must contain at least one uppercase letter."]}, status=status.HTTP_400_BAD_REQUEST)
        if not any(char.islower() for char in password):
            return Response({"password": ["Password must contain at least one lowercase letter."]}, status=status.HTTP_400_BAD_REQUEST)
        if not any(char.isdigit() for char in password):
            return Response({"password": ["Password must contain at least one number."]}, status=status.HTTP_400_BAD_REQUEST)
        if not any(char in '!@#$%^&*()-_=+[]{}|;:,.<>?/' for char in password):
            return Response({"password": ["Password must contain at least one special character."]}, status=status.HTTP_400_BAD_REQUEST)

        # Check if username already exists
        username = request.data.get('username')
        if User.objects.filter(username=username).exists():
            return Response({"username": ["A user with that username already exists."]}, status=status.HTTP_400_BAD_REQUEST)

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return Response({"email": ["A user with that email already exists."]}, status=status.HTTP_400_BAD_REQUEST)

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', '')
        )

        # Create client profile automatically
        client_data = request.data.get('client_profile', {})
        if client_data:
            # ✅ CORRECCIÓN: No agregues 'user' a client_data
            client_data['email'] = email  # Use the same email as the user
            client_serializer = ClientSerializer(data=client_data)
            if client_serializer.is_valid():
                # ✅ CORRECCIÓN: Pasa el user directamente al save()
                client_serializer.save(user=user)
            else:
                # Si falla la creación del cliente, eliminar el usuario creado
                user.delete()
                return Response({
                    'client_profile': client_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        # Crear data de respuesta usando el user creado
        user_data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

        return Response({
            'user': user_data,
            'message': 'User created successfully'
        }, status=status.HTTP_201_CREATED)


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Clients.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        """
        Permisos diferenciados según el tipo de acción
        """
        if self.action in ['list', 'destroy']:
            # Solo admin puede listar todos los clientes o eliminar
            permission_classes = [IsAdminUser]
        elif self.action == 'create':
            # Cualquier usuario autenticado puede crear un cliente
            permission_classes = [IsAuthenticated]
        else:
            # Para retrieve, update, partial_update - verificar en el método
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filtrar queryset según el usuario
        """
        if self.request.user.is_staff:
            return Clients.objects.all()
        else:
            # Los usuarios normales solo pueden ver su propio perfil
            return Clients.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Asociar el cliente con el usuario actual al crear
        """
        # Verificar si el usuario ya tiene un perfil de cliente
        if Clients.objects.filter(user=self.request.user).exists():
            raise ValidationError("You already have a client profile.")

        serializer.save(user=self.request.user)

    def retrieve(self, request, pk=None):
        """
        Verificar permisos para ver un cliente específico
        """
        client = self.get_object()

        if not request.user.is_staff and client.user != request.user:
            return Response(
                {"detail": "You don't have permission to view this client profile."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(client)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Verificar permisos para actualizar un cliente
        """
        client = self.get_object()

        if not request.user.is_staff and client.user != request.user:
            return Response(
                {"detail": "You don't have permission to update this client profile."},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Verificar permisos para actualización parcial
        """
        client = self.get_object()

        if not request.user.is_staff and client.user != request.user:
            return Response(
                {"detail": "You don't have permission to update this client profile."},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().partial_update(request, *args, **kwargs)


class RoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    # Solo los administradores pueden crear o eliminar habitaciones
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def availability(self, request):
        """
        Consultar disponibilidad de habitaciones en fechas específicas
        """
        date_in = request.query_params.get('date_in')
        date_out = request.query_params.get('date_out')
        guests = request.query_params.get('guests', 1)
        room_type = request.query_params.get('room_type')

        # Validar parámetros requeridos
        if not date_in or not date_out:
            return Response(
                {"error": "date_in and date_out parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Convertir strings a objetos date
            date_in = datetime.strptime(date_in, '%Y-%m-%d').date()
            date_out = datetime.strptime(date_out, '%Y-%m-%d').date()
            guests = int(guests)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar fechas
        if date_out <= date_in:
            return Response(
                {"error": "date_out must be after date_in"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if date_in < date.today():
            return Response(
                {"error": "date_in cannot be in the past"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener habitaciones disponibles
        available_rooms = Room.objects.filter(
            status='available',
            capacity__gte=guests
        )

        # Filtrar por tipo de habitación si se especifica
        if room_type:
            available_rooms = available_rooms.filter(type=room_type)

        # Excluir habitaciones con reservaciones en conflicto
        conflicting_reservations = Reservation.objects.filter(
            date_in__lt=date_out,
            date_out__gt=date_in,
            status__in=['pending', 'confirmed']
        ).values_list('room_id', flat=True)

        available_rooms = available_rooms.exclude(
            id__in=conflicting_reservations)

        # Calcular precio total para cada habitación
        nights = (date_out - date_in).days
        results = []
        for room in available_rooms:
            total_price = nights * room.price_for_night
            results.append({
                'room_id': room.id,
                'room_number': room.number,
                'room_type': room.type,
                'capacity': room.capacity,
                'price_per_night': room.price_for_night,
                'total_price': total_price,
                'nights': nights,
                'description': room.description,
                'amenities': room.amenities
            })

        return Response({
            'date_in': date_in,
            'date_out': date_out,
            'guests': guests,
            'available_rooms': results,
            'total_available': len(results)
        })


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        """
        Permisos diferenciados según el tipo de acción
        """
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            # Solo admin puede crear, eliminar o modificar reservaciones
            permission_classes = [IsAdminUser]
        else:
            # Consultas y listados requieren solo autenticación
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def list(self, request):
        """
        Listar reservaciones (solo usuarios autenticados)
        """
        # Filtrar reservaciones según el usuario
        if request.user.is_staff:
            # Admins ven todas las reservaciones
            queryset = Reservation.objects.all()
        else:
            # Usuarios normales ven solo sus propias reservaciones
            try:
                client = Clients.objects.get(user=request.user)
                queryset = Reservation.objects.filter(client=client)
            except Clients.DoesNotExist:
                queryset = Reservation.objects.none()

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Detalle de reservación (solo usuarios autenticados)
        """
        reservation = self.get_object()

        # Verificar si el usuario tiene permiso para ver esta reservación
        if not request.user.is_staff:
            try:
                client = Clients.objects.get(user=request.user)
                if reservation.client != client:
                    return Response(
                        {"detail": "No tiene permiso para ver esta reservación"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Clients.DoesNotExist:
                return Response(
                    {"detail": "No tiene permiso para ver esta reservación"},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = self.get_serializer(reservation)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def my_reservations(self, request):
        """
        Acción personalizada para ver reservaciones del usuario actual
        """
        try:
            client = Clients.objects.get(user=request.user)
            queryset = Reservation.objects.filter(client=client)
        except Clients.DoesNotExist:
            queryset = Reservation.objects.none()

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
