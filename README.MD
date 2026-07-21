## Cómo restaurar la base de datos

1. Descarga el archivo `.bak` desde este link: [pega aquí tu link de Drive](el link es privado asi que el que quiera copiar esto.. jodase)
2. Abre SQL Server Management Studio (SSMS)
3. Clic derecho en "Bases de datos" → Restaurar base de datos...
4. Selecciona "Dispositivo" → busca el archivo .bak descargado
5. En "Base de datos de destino" escribe: Sistema Biblioteca universitaria
6. Aceptar

## Cómo correr el proyecto

1. Clona este repositorio
2. Crea un entorno virtual: `py -m venv venv`
3. Actívalo: `.\venv\Scripts\Activate`
4. Instala dependencias: `pip install -r requirements.txt`
5. Copia `.env.example` a `.env` y coloca tus propios datos de conexión
   (usuario y contraseña de TU instalación de SQL Server)
6. Corre: `python manage.py runserver`
