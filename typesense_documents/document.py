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
        collections = self.typesense_client.collections.retrieve()
        exists = False
        for collection in collections:
            if collection["name"] == self.collection_name:
                exists = True
                break
        if exists:
            self.typesense_client.collections[self.collection_name].delete()

        self.typesense_client.collections.create(self.collection_schema)

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
        for obj in queryset:
            try:
                documents.append(self.prepare_collection_document(obj))
            except TypeError:
                continue
        print(f"Indexing {self.Meta.model.__name__}. Total documents: {len(documents)}...")
        for document in documents:
            self.typesense_client.collections[self.collection_name].documents.create(document)

    def init_collection(self):
        self.create_collection()
        self.fill_collection()
        print(f"Collection {self.collection_name} created")

    def update_document(self, instance):
        index_document_id = getattr(instance, self.Meta.id_field or "pk")
        if index_document_id:
            index_document_id = str(index_document_id)
            index_document_update = self.prepare_collection_document(instance)
            self.typesense_client.collections[self.collection_name].documents[index_document_id].update(
                index_document_update
            )

    def delete_document(self, instance):
        index_document_id = getattr(instance, self.Meta.id_field or "pk")
        if index_document_id:
            index_document_id = str(index_document_id)
            try:
                self.typesense_client.collections[self.collection_name].documents[index_document_id].delete()
            except Exception:
                pass
