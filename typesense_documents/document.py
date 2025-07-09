import typesense
from django.conf import settings
from typesense_documents.fields import BaseField, EmbeddingField


class TypesenseDocument:
    collection_name = None
    default_sorting_fields = None

    fields = []

    def parse_attributes(self):
        self.fields = {}
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, BaseField):
                self.fields[name] = value
            if name == "collection_name":
                self.collection_name = value
            if name == "default_sorting_fields":
                self.default_sorting_fields = value

    def __init__(self):
        self.parse_attributes()
        self.collection_schema = self.get_collection_schema()
        self.typesense_client = typesense.Client(
            {
                "nodes": [
                    {
                        "host": settings.TYPESENSE_HOST,
                        "port": settings.TYPESENSE_PORT,
                        "protocol": settings.TYPESENSE_PROTOCOL,
                    }
                ],
                "api_key": settings.TYPESENSE_API_KEY,
                "connection_timeout_seconds": 2,
            }
        )

    def get_collection_schema(self):
        schema = {"name": self.collection_name}
        if self.default_sorting_fields:
            schema["default_sorting_fields"] = self.default_sorting_fields
        fields_schema_list = []
        for name, field_type in self.fields.items():
            field_schema = field_type.get_field_schema()
            field_schema["name"] = name
            fields_schema_list.append(field_schema)
        schema["fields"] = fields_schema_list
        return schema

    def create_collection(self):
        try:
            collections = self.typesense_client.collections.retrieve()
            exists = False
            for collection in collections:
                if collection["name"] == self.collection_name:
                    exists = True
                    break
            if exists:
                self.typesense_client.collections[self.collection_name].delete()

            self.typesense_client.collections.create(self.collection_schema)
        except:
            pass

    def prepare_collection_document(self, obj):
        fields = self.fields
        document = {}
        embeddings = []
        for name, field_type in fields.items():
            if isinstance(field_type, EmbeddingField):
                embeddings.append(field_type)
                continue
            value = field_type.value
            if value is None:
                value = name
            attr = getattr(obj, value)
            if callable(attr):
                attr = attr()
            document[name] = field_type.prepare_value(attr)
        for embedding in embeddings:
            embed_field = embedding.from_field
            embed_value = document.get(embed_field)
            if embed_value is None:
                raise TypeError
        id_field = self.Meta.id_field or "pk"
        id_attr = getattr(obj, id_field)

        if id_attr is not None:
            document["id"] = str(id_attr)
            return document
        raise TypeError

    def get_queryset(self):
        meta_model = self.Meta.model
        return meta_model.objects.all()

    def prepare_first_object(self):
        queryset = self.get_queryset()
        obj = queryset.first()
        return self.prepare_collection_document(obj)

    def fill_collection(self):
        queryset = self.get_queryset()
        documents = []
        print(f"Indexing {self.Meta.model.__name__}.")
        counter = 0
        for obj in queryset:
            try:
                document = self.prepare_collection_document(obj)
                if document is not None:
                    self.typesense_client.collections[self.collection_name].documents.create(document)
                    counter += 1
            except TypeError:
                continue
        print(f"Total documents: {counter}...")

    def init_collection(self):
        self.create_collection()
        self.fill_collection()
        print(f"Collection {self.collection_name} created")

    def update_document(self, instance):
        index_document_id = getattr(instance, self.Meta.id_field or "pk")
        if index_document_id:
            index_document_id = str(index_document_id)
            index_document_update = self.prepare_collection_document(instance)
            self.typesense_client.collections[self.collection_name].documents[index_document_id].update(index_document_update)

    def delete_document(self, instance):
        index_document_id = getattr(instance, self.Meta.id_field or "pk")
        if index_document_id:
            index_document_id = str(index_document_id)
            try:
                self.typesense_client.collections[self.collection_name].documents[index_document_id].delete()
            except Exception:
                pass

    def search(self, q, query_by, sort_by, query_by_weights=None, per_page=50, page=1, filter_by=None, text_match_type=None):
        search_parameters = {
            "q": q,
            "query_by": query_by,
            "sort_by": sort_by,
            # "query_by_weights": query_by_weights,
            # "per_page": per_page,
            # "page": page,
            # "filter_by": filter_by,
            # "text_match_type": text_match_type,
        }

        search_response = self.typesense_client.collections[self.collection_name].documents.search(search_parameters)
        return_data = {"count": search_response.get("found"), "num_page": page}
        results = []
        hits = search_response.get("hits")
        for hit in hits:
            document = hit.get("document")
            result_object = {"id": document.get("pk"), "score": hit.get("text_match"), "resource_type": "product"}
            print(f"{document.get('pk')} {document.get('sku')} {result_object.get('score')}")
            results.append(result_object)
        return_data["search_results"] = results
        return return_data

    def multi_search(self, q, params):
        pass
