import pyodbc
import requests
import csv

# URL de la API para obtener las películas populares
api_url = "https://api.themoviedb.org/3/movie/popular?language=en-US"

# Tu api_key de la API de TMDB
api_key = "poner tu api key"

# Conexión a SQL Server
conexion = pyodbc.connect('DRIVER={SQL Server};'
                          'SERVER=poner nombre del servidor;'
                          'DATABASE=TMDB;'
                          'UID=santiago;'
                          'PWD=contraseña')
cursor = conexion.cursor()

# Función para determinar la categoría de popularidad
def categorizar_popularidad(popularity):
    if popularity < 1000:
        return "BAJA"
    elif popularity < 5000:
        return "MEDIA"
    else:
        return "ALTA"

# Función para actualizar o insertar la categoría de popularidad
def actualizar_popularidad(movie_id, title, popularity_category):
    query = """
    IF EXISTS (SELECT 1 FROM MoviePopularity WHERE movie_id = ?)
    BEGIN
        -- Si existe, actualizamos la categoría de popularidad
        UPDATE MoviePopularity 
        SET popularity_category = ? 
        WHERE movie_id = ? 
    END
    ELSE
    BEGIN
        -- Si no existe, insertamos el nuevo registro
        INSERT INTO MoviePopularity (movie_id, title, popularity_category)
        VALUES (?, ?, ?)
    END
    """
    cursor.execute(query, (movie_id, popularity_category, movie_id, movie_id, title, popularity_category))
    conexion.commit()
    print(f"La categoría de popularidad para la película con ID {movie_id} se ha actualizado a {popularity_category}.")

# Función para insertar la película si no existe en la tabla Movies
def insertar_pelicula_si_no_existe(movie_id, title, release_date, original_language, vote_average, vote_count, popularity, overview, genre_ids):
    cursor.execute("SELECT COUNT(*) FROM Movies WHERE id = ?", (movie_id,))
    existe = cursor.fetchone()[0]

    if existe == 0:
        query = """
        INSERT INTO Movies (id, titulo, fecha_estreno, idioma_original, voto_promedio, numero_votos, popularidad, overview, generos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (movie_id, title, release_date, original_language, vote_average, vote_count, popularity, overview, genre_ids))
        conexion.commit()
        print(f"La ID {movie_id} se ha insertado exitosamente en Movies.")
    else:
        print(f"La ID {movie_id} ya existe en la tabla Movies.")

# Función para obtener películas populares de TMDB y procesarlas
def obtener_peliculas(api_url, api_key, num_paginas=1):
    movie_data = []  # Para almacenar los datos de las películas para CSV
    popularity_data = []  # Para almacenar los datos de MoviePopularity para CSV

    for pagina in range(1, num_paginas + 1):
        url = f"{api_url}&page={pagina}&api_key={api_key}"
        print(f"Obteniendo datos de la página {pagina}...")

        try:
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()

                if 'results' in data:
                    count = 0

                    for pelicula in data['results']:
                        movie_id = pelicula['id']
                        title = pelicula['title']
                        release_date = pelicula['release_date']
                        original_language = pelicula['original_language']
                        vote_average = pelicula['vote_average']
                        vote_count = pelicula['vote_count']
                        popularity = pelicula['popularity']
                        overview = pelicula['overview']
                        genre_ids = ','.join(str(genre) for genre in pelicula['genre_ids'])

                        # Obtener la categoría de popularidad
                        popularity_category = categorizar_popularidad(popularity)

                        # Insertar la película en Movies si no existe
                        insertar_pelicula_si_no_existe(movie_id, title, release_date, original_language, vote_average, vote_count, popularity, overview, genre_ids)

                        # Actualizar o insertar la categoría de popularidad
                        actualizar_popularidad(movie_id, title, popularity_category)

                        # Guardar los datos para el CSV
                        movie_data.append([movie_id, title, release_date, original_language, vote_average, vote_count, popularity, overview, genre_ids])
                        popularity_data.append([movie_id, title, popularity_category])

                        count += 1
                    
                    print(f"Página {pagina}: {count} resultados encontrados.")
                else:
                    print(f"No se encontraron resultados en la página {pagina}.")
            else:
                print(f"Error en la solicitud de la página {pagina}. Código de estado: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Ocurrió un error al hacer la solicitud para la página {pagina}: {e}")

    # Guardar los datos de películas en un archivo CSV
    with open('movies.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['id', 'titulo', 'fecha_estreno', 'idioma_original', 'voto_promedio', 'numero_votos', 'popularidad', 'overview', 'generos'])
        writer.writerows(movie_data)

    # Guardar los datos de popularidad en un archivo CSV
    with open('movie_popularity.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['id', 'titulo', 'categoria_popularidad'])
        writer.writerows(popularity_data)

    # Mensajes de confirmación
    print("El archivo 'movies.csv' ha sido creado exitosamente.")
    print("El archivo 'movie_popularity.csv' ha sido creado exitosamente.")

# Llamamos a la función para obtener las películas populares desde las primeras 5 páginas
obtener_peliculas(api_url, api_key, num_paginas=10)

# Cerrar la conexión a la base de datos
conexion.close()