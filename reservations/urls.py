from rest_framework.routers import DefaultRouter
from django.urls import path, include
from reservations.views import ClientViewSet, RoomViewSet, ReservationViewSet, RegisterUser

app_name = "reservations"
router = DefaultRouter()
router.register(r'client', ClientViewSet, basename="client")
router.register(r'room', RoomViewSet, basename="room")
router.register(r'reservation', ReservationViewSet, basename="reservation")
router.register(r'register', RegisterUser, basename="register")

urlpatterns = [
    path('', include(router.urls)),
    path('reservation/my_reservations/', ReservationViewSet.as_view(
        {'get': 'my_reservations'}), name='reservation-my_reservations'),
    path('room/availability/', RoomViewSet.as_view(
        {'get': 'availability'}), name='room-availability')
]
