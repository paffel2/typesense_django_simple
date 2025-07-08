class CollectionRegistry:
    def __init__(self):
        self.index = set()
        self.models = set()

    def register_model(self, document):
        self.index.add(document)
        self.models.add(document.Meta.model)

    def update(self, instance):
        if instance.__class__ in self.models:
            for index_class in self.index:
                if index_class.Meta.model == instance.__class__:
                    index_class().update_document(instance)

    def delete(self, instance):
        if instance.__class__ in self.models:
            for index_class in self.index:
                if index_class.Meta.model == instance.__class__:
                    index_class().delete_document(instance)


typesense_registry = CollectionRegistry()
