insert_into_elastic_search lee las noticias contenidas en una base de datos Mongo y las inserta en un indice de ElasticSearch previamente creado.

insert_paragraphs_into_elastic_search.py lee los documentos en un indice elastic_search, los descompone en párrafos e inserta esos párrafos en elastic_search. Este nuevo indice contiene adicionalmente el identificador del documento del indice del cual se extraen los documentos a descomponer en parrafos.
