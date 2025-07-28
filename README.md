# Sistema de Reserva de Habitaciones

Un robusto sistema backend para gestionar reservas de habitaciones en hoteles y alojamientos, desarrollado con Django y DRF

## Características

### Características principales

- Sistema completo de gestión de habitaciones
- Autenticación y autorización de usuarios
- Gestión de reservas con seguimiento de estado
- Documentación API con Swagger y Redoc
- Autenticación basada en JWT

### Gestión de habitaciones

- Diferentes tipos de habitación (Individual, Doble, Twin, Suite, Deluxe)
- Seguimiento del estado de la habitación (Disponible, Reservada, Limpieza, Mantenimiento)
- Gestión de precios por noche
- Gestión de capacidad
- Seguimiento de los servicios de la habitación

### Gestión de clientes

- Gestión de perfiles de clientes
- Almacenamiento de información de contacto
- Seguimiento del número de documento
- Gestión de direcciones
- Validación de correo electrónico y teléfono

### Sistema de reservas

- Validación de rango de fechas
- Consulta de disponibilidad de habitaciones con estado en tiempo real
- Validación de capacidad con seguimiento del número de huéspedes
- Seguimiento del estado de la reserva (Pendiente, Confirmada, Cancelada)
- Cálculo automático de precios basado en noches y tarifa de la habitación
- Validación del número de huéspedes
- Prevención de solapamiento en reservas conflictivas
- Consideración del estado de la habitación (mantenimiento, limpieza)

### Características de seguridad

- Control de acceso basado en roles
- Token JWT Autenticación
- Compatibilidad con lista negra de tokens
- Hash de contraseñas seguro
- Validación de unicidad de correo electrónico

## Stack técnico

### Backend

- Django 5.1.5
- Framework REST de Django
- Django Simple JWT
- DRF Spectacular para la documentación de la API
- Python 3.12

### Dependencias

- rest_framework
- rest_framework_simplejwt
- drf_spectacular
- phonenumber_field

## Puntos finales de la API

### Autenticación

- POST /api/token/ - Obtener token JWT
- POST /api/token/refresh/ - Actualizar token JWT

### Salas

- GET /room/ - Listar todas las salas (usuarios autenticados)
- POST /room/ - Crear nueva sala (solo administrador)
- GET /room/{id}/ - Obtener detalles de la sala (usuarios autenticados)
- PUT /room/{id}/ - Actualizar sala (solo administrador)
- DELETE /room/{id}/ - Eliminar sala (solo administrador)
- GET /room/availability/ - Consultar disponibilidad de salas para fechas específicas

### Clientes

- GET /client/ - Listar clientes (el administrador ve todos, los usuarios ven su propio perfil)
- POST /client/ - Crear nuevo perfil de cliente (usuarios autenticados)
- GET /client/{id}/ - Obtener detalles del cliente (perfil propio o administrador)
- PUT /client/{id}/ - Actualizar cliente (perfil propio o administrador)
- DELETE /client/{id}/ - Eliminar cliente (solo administrador)

### Reservas

- GET /reservation/ - Listar reservas (el administrador ve todas, los usuarios ven su propia)
- POST /reservation/ - Crear nueva reserva (solo administrador)
- GET /reservation/{id}/ - Obtener detalles de la reserva (reservas propias o administrador)
- PUT /reservation/{id}/ - Actualizar reserva (solo administrador)
- DELETE /reservation/{id}/ - Eliminar reserva (solo administrador)
- GET /reservation/my_reservations/ - Obtener las reservas del usuario actual

### Registro de usuario

- POST /register/ - Registrar un nuevo usuario con la opción de crear un perfil de cliente

Instrucciones de configuración

1. Clonar el repositorio
2. Instalar UV (gestor de paquetes de Python):

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3. Instalar dependencias:

    ```bash
    uv sync
    ```

4. Activar el entorno virtual:

    ```bash
    source .venv/bin/activate # En Windows: .venv\Scripts\activate
    ```

5. Configurar las variables de entorno:

   - Crear un archivo `.env` en la raíz del proyecto.
   - Agregar las siguientes variables:

   ```.env
   SECRET_KEY=your_secret_key
   DEBUG=True
   SIGNING_KEY=your_signing_key
   DATABASE_URL=postgresql://user:password@localhost:5432/database_name
   ```

6. Aplicar migraciones:

    ```bash
    python manage.py migration
    ```

7. Crear un superusuario (opcional):

    ```bash
    python manage.py createsuperuser
    ```

8. Ejecutar el servidor de desarrollo:

    ```bash
    python manage.py runserver
    ```

## Documentación de la API

La API está documentada con DRF Spectacular. Puede acceder a la documentación en:

- Interfaz de usuario de Swagger: [http://localhost:8000/swagger/]
- Interfaz de usuario de ReDoc: [http://localhost:8000/redoc/]

## Notas de seguridad

- Todos los endpoints requieren autenticación, excepto para el registro de usuarios.
- Se requieren privilegios de administrador para crear, actualizar o eliminar habitaciones y reservas.
- Los usuarios solo pueden ver y administrar sus propios perfiles de cliente y reservas.
- Se aplican requisitos de contraseña segura (más de 8 caracteres, mayúsculas, minúsculas, números y caracteres especiales).
- Validación de la unicidad del correo electrónico y el nombre de usuario.
- Los tokens JWT tienen un plazo de caducidad de 2 horas.
- Los tokens de actualización tienen una validez de 30 días.
- Creación automática de perfiles de cliente durante el registro de usuario.
- Validación de la unicidad del número de documento para clientes.

## Nuevas funciones añadidas

### Sistema de reservas mejorado

- **Seguimiento del número de huéspedes**: Las reservas ahora incluyen el número de huéspedes con validación de capacidad.
- **Cálculo automático de precios**: El precio total se calcula automáticamente en función de las noches y la tarifa de la habitación.
- **Consulta avanzada de disponibilidad**: El estado de la habitación (mantenimiento, limpieza) se tiene en cuenta para la disponibilidad.
- **API de disponibilidad en tiempo real**: Nuevo punto de acceso para consultar la disponibilidad de habitaciones en rangos de fechas específicos.

### Gestión de usuarios mejorada

- **Registro mejorado**: Los usuarios pueden crear perfiles de cliente durante el registro.
- **Integración de perfiles**: Vinculación automática entre cuentas de usuario y perfiles de cliente.
- **Control de acceso seguro**: Los usuarios solo pueden acceder a sus propios datos, a menos que sean administradores.

### Sistema de disponibilidad de habitaciones

- **Consulta de disponibilidad**: Punto de acceso GET /room/availability/ con los siguientes parámetros:
- `date_in`: Fecha de entrada (AAAA-MM-DD)
- `date_out`: Fecha de salida (AAAA-MM-DD)
- `guests`: Número de huéspedes (opcional, predeterminado: 1)
- `room_type`: Filtrar por tipo de habitación (opcional)
- **Resultados en tiempo real**: Muestra las habitaciones disponibles con información de precios
- **Filtrado completo**: Considera el estado de las habitaciones, las reservas existentes y la capacidad

### Validación de datos mejorada

- **Unicidad del número de documento**: Evita la duplicación de números de documento del cliente
- **Validación de correo electrónico**: Formato de correo electrónico mejorado y verificación de unicidad
- **Validación de fecha**: Evita reservas con fecha vencida y rangos de fechas no válidos
- **Validación de capacidad**: Garantiza que el número de huéspedes no exceda la capacidad de la habitación

### Conjunto de pruebas

- **Cobertura completa de pruebas**: Pruebas unitarias para modelos, serializadores y endpoints de API
- **Pruebas de autenticación**: Pruebas de autenticación y autorización JWT
- **Pruebas de validación**: Pruebas para todas las reglas de validación de datos
- **Pruebas de integración de API**: Pruebas de funcionalidad de API de extremo a extremo

## Ejemplos de uso

### Consultar disponibilidad de habitaciones

```bash
GET /room/availability/?date_in=2024-12-25&date_out=2024-12-27&guests=2&room_type=double
```

### Registrar usuario con perfil de cliente

```json
POST /register/
{
"username": "johndoe",
"email": "john@example.com",
"password": "¡SecurePass123!",
"confirm_password": "¡SecurePass123!",
"first_name": "John",
"last_name": "Doe",
"client_profile": {
"name": "John",
"lastname": "Doe",
"document_number": "12345678",
"street": "123 Main St",
"city": "New" York",
"estado": "NY",
"país": "EE. UU.",
"teléfono": "+1234567890"
}
}
```

### Crear reserva (solo administrador)

```json
POST /reservation/
{
"fecha_entrada": "2024-12-25",
"fecha_salida": "2024-12-27",
"número_de_huéspedes": 2,
"cliente": 1,
"habitación": 101
}
```

## Pruebas

Ejecutar el conjunto de pruebas con:

```bash
python manage.py test
```

Ejecutar pruebas con cobertura:

```bash
pytest --cov=reservations --cov-report=html
```

## Contribución

1. Bifurcar el repositorio
2. Crear la rama de funciones (`git checkout -b feature/amazing-feature`)
3. Escribe pruebas para tu nueva característica
4. Asegúrate de que todas las pruebas sean correctas (`python manage.py test`)
5. Confirma los cambios (`git commit -m 'Add some amazing feature'`)
6. Sube a la rama (`git push origin feature/amazing-feature`)
7. Abre una solicitud de extracción

## Licencia

Este proyecto está licenciado bajo la licencia MIT; consulta el archivo LICENSE para más detalles.
