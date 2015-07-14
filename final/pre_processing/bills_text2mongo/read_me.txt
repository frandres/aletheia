process_bills_spanish.py lee las leyes de un directorio y prepara un documento Mongo para cada ley con los siguientes campos:

+ title
+ text.
+ year.
+ keywords.
+ id.

De estos campos, todos menos keywords son generados con expresiones regulares. Las keywords son extraidas utilizando tf-idf como sigue:

1. Se consideran n-grams de tamaño 1,2,3.
2. Se calcula el valor TF-IDF de cada n-gram según su frecuencia en cada ley y en todo el conjunto de documentos.
3. Se guardan para cada ley las 1000 keywords con mayor peso.
