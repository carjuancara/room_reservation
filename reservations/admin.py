from django.contrib import admin
from reservations.models import Clients, Room, Reservation


@admin.register(Clients)
class ClientsAdmin(admin.ModelAdmin):
    list_display = ['name', 'lastname', 'email', 'phone', 'document_number', 'country', 'user', 'created_at']
    list_filter = ['country', 'created_at']
    search_fields = ['name', 'lastname', 'email', 'document_number']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['number', 'type', 'status', 'capacity', 'price_for_night', 'is_reserved']
    list_filter = ['type', 'status', 'capacity']
    search_fields = ['number', 'type', 'description']
    list_editable = ['status', 'is_reserved']
    ordering = ['number']


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'room', 'date_in', 'date_out', 'number_of_guests', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at', 'date_in', 'room__type']
    search_fields = ['client__name', 'client__lastname', 'room__number']
    readonly_fields = ['created_at', 'updated_at', 'total_price']
    date_hierarchy = 'date_in'
    ordering = ['-created_at']

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['client', 'room']
        return self.readonly_fields
