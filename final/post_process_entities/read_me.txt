post_process_entities contiene varias funciones para postprocesar las entidades y preparar la generacion de grafos:

+ set_main_tag: determina el tipo de una entidad (organizacion, persona, localizacion) segun el tag más frecuentemente asignado.

+ normalize_locations: intenta llevar nombres de ubicaciones que estan en mayusculas a una versión camelizada.

+ get_entities_documents: para cada entidad y ley, determina en qué documentos aparece la entidad y lo almacena en Mongo.

+ get_entities_keywords: dado una ley, modela cada entidad como un vector de keywords extraidos de cada párrafo de cada documento relacionado con la ley en los que aparezca la entidad.

Adicionalmente, tiene las siguientes dos funciones que permiten, con intervención humana, mejorar los resultados:

+ eliminate_duplicated_entities: permite desambiguar manualmente entidades haciendo fuzzy matching de los nombres. Dado dos nombres que se parecen, se puede descartar una de las entidades para el análisis de una ley.

+ fix_tags: permite verificar que la clasificación de una entidad (organización, etc) sea correcta.

post_process_entities tiene las siguientes dependencias:

+ fiter_entities.py contiene la lógica para determinar cuáles son las entidades relevantes para cada tema, utilizando Latent Semantic Index y Hierarchical Agglomerative Clustering.

+ entities_functions.py: contiene una unica funcion para unificar entidades que tengan el mismo nombre.

+ metrics: continee la lógica para calcular medidas de similaridad entre dos entidades. Tiene varias métricas implementadas que se almacenan en la colección entity_entity

+ insert_politicians.py es un script que tiene que ser invocado para cada ley que se analice con el objetivo de insertar en la base de datos los politicos que participaron en la redacción de la ley. Idealmente esta información se puede obtener de forma automatizada de los datos del parlament; por restricciones de tiempo no implementé esta función y en su lugar inserte los políticos para cada ley que analice manualmente. Esta lista de políticos es importante para la función filter_entities.
