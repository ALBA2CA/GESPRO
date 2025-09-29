# Gespro: Manual de Despliegue

Este manual describe las dos opciones principales para el despliegue de la aplicación Gespro: utilizando **Docker** para un inicio rápido y aislado, o clonando el **Repositorio** para un entorno de desarrollo o despliegue personalizado.

---

## Opción 1: Despliegue con Docker (Recomendado)

La forma más rápida y sencilla de poner en marcha Gespro es utilizando nuestra imagen oficial de **Docker Hub**. Esto asegura que todas las dependencias y el entorno estén preconfigurados correctamente.

### Requisitos

- **Docker** 
- **Docker Compose**

### Pasos de Despliegue

1.  **Obtener la Imagen:** Descarga la imagen de Gespro desde Docker Hub.

    ```bash
    docker pull osvaldoccn/gespro_web:latest 
    ```

2.  **Ejecutar el Contenedor:** Inicia la aplicación en un contenedor aislado.

    ```bash
    docker run -d -p 8000:8000 --name gespro-app osvaldoccn/gespro_web:latest
    ```

---

## Opción 2: Despliegue desde el Repositorio

Esta opción es ideal para **desarrolladores** o para entornos que requieren una configuración detallada y control total sobre las dependencias.

###  Requisitos y Dependencias

Asegúrate de tener instaladas las siguientes herramientas en tu sistema:

* **Python:** Versión `3.11.x`
* **Node.js:** Necesario para el *frontend* y la compilación de Tailwind CSS.

#### Librerías de Python

Las librerías de Python requeridas se encuentran detalladas en el archivo `requirements.txt`.

```txt
asgiref==3.9.1
Django==5.2.6
django-browser-reload==1.18.0
django-tailwind==4.2.0
django-widget-tweaks==1.5.0
et_xmlfile==2.0.0
openpyxl==3.1.5
pandas==2.3.2
psycopg==3.2.9
psycopg2-binary==2.9.10
python-dateutil==2.9.0.post0
pytz==2025.2
six==1.17.0
sqlparse==0.5.3
typing_extensions==4.15.0
tzdata==2025.2 
```

### Pasos de Instalación y Configuración

Asegúrate de estar en el directorio **raíz** del proyecto antes de comenzar.

1.  **Clonar el Repositorio:** Descarga el código fuente.

    ```bash
    git clone https://github.com/ALBA2CA/GESPRO.git 
    cd GESPRO
    ```

2.  **Instalar Dependencias de Python:** Es altamente recomendable usar un **entorno virtual** para aislar las dependencias del proyecto.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuración de Tailwind CSS:** Accede a la carpeta `backend` para instalar y compilar los archivos de estilo.

    ```bash
    cd backend
    # Instalar Tailwind CSS para que el motor de Django lo reconozca
    python manage.py tailwind install
    # Compilar los archivos CSS estáticos
    python manage.py tailwind build
    ```

4.  **Preparación de la Base de Datos:** Aplica las migraciones para crear el esquema de la base de datos.
    ```bash
    python manage.py migrate
    ```

5.  **Iniciar Servicios:**

    * **Encender Trabajadores de Tareas Calendarizadas (Django-Q):** Este servicio maneja las tareas asíncronas y programadas.

        ```bash
        python manage.py djangoQ cluster
        ```

    * **Correr el Servidor Web:** Inicia la aplicación principal.

        ```bash
        # El servidor correrá por defecto en [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
        python manage.py runserver [ip:puerto]
        ```
        * Reemplaza `[ip:puerto]` con la dirección y puerto deseados, si es diferente al predeterminado.
