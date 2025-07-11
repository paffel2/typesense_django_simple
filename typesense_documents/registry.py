class CollectionRegistry:
    def __init__(self):
        self.index = set()
        self.models = set()
        self.related_models = {}

    def register_model(self, document):
        self.index.add(document)
        self.models.add(document.Meta.model)
        if document.Meta.related_models:
            for related_model in document.Meta.related_models:
                if related_model not in self.related_models:
                    self.related_models[related_model] = set([document])
                else:
                    self.related_models[related_model].add(document)

    def update(self, instance):
        if instance.__class__ in self.models:
            for index_class in self.index:
                if index_class.Meta.model == instance.__class__:
                    index_class().update_document(instance)

        if instance.__class__ in self.related_models:
            for document in self.related_models[instance.__class__]:
                if document in self.index:
                    document_instance = document()
                    related_for_update = document_instance.get_instances_from_related(instance)
                    for related_instance in related_for_update:
                        document_instance.update_document(related_instance)

    def delete(self,instance_pk, model_name):
        for model in typesense_registry.models:
            if model.__name__ == model_name:
                for index_class in self.index:
                    if index_class.Meta.model == model.__class__:
                        index_class().delete_document(instance_pk)

    def get_model_pk(self,instance):
        if instance.__class__ in self.models:
            for index_class in self.index:
                if index_class.Meta.model == instance.__class__:
                    return getattr(instance, index_class.Meta.id_field or "pk")

typesense_registry = CollectionRegistry()
