search_articles.py extrae entidades relevantes para cada una de las leyes y las almacena en una base de datos Mongo en las siguientes colecciones:

+ entities: almacena la información básica de cada entidad.
+ entities_bills: almacena la interrelación entre una entidad y una ley y cualquier información relevante de esa interrelación.
+ entities

search_articles.py tiene las siguientes dependencias:

+ rocchio.py: utiliza Rocchio's rule para descubrir nuevas keywords a partir de los articulos de prensa.

+ entities.py: contiene la lógica para extraer entidades de un articulo (get_entities). Utiliza MITIE como punto de partida y además implementa funciones para mejorar la calidad de los nombres.

+ entities_functions.py: contiene una unica funcion para unificar entidades que tengan el mismo nombre.
