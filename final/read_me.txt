elastic_search y mongo contienen los scripts de creación de indices de elasticsearch y de mongo, asi como una definición del esquema utilizado en MongoDB.

El resto de las carpetas contienen los scripts de Python del sistema. En cada carpeta hay un read_me que explica la funcionalidad de cada paquete.

El orden de todo el sistema es: 

1) pre_processing -> pre-processing del diagrama (downloading and indexing bills, modelling topics from bills, downloading an indexing articles).
2) analyze_bill. (finding news articles related to the bills, finding entities)
3) post_process_entities. (filtering entities, finding politicians related to a bill)
4) generate_graph (generating the entity-entity graph).
