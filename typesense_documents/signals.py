from typesense_documents.registry import typesense_registry
from django.db import models
from celery import shared_task


class SignalProcessor:
    def __init__(self):
        models.signals.post_save.connect(self.handle_save)
        models.signals.post_delete.connect(self.handle_delete)
        models.signals.m2m_changed.connect(self.handle_m2m_changed)

    def handle_save(self, sender, instance, **kwargs):
        typesense_registry.update(instance)

    def handle_delete(self, sender, instance, **kwargs):
        instance_pk = typesense_registry.get_model_pk(instance)
        typesense_registry.delete(instance_pk, instance.__class__.__name__)

    def handle_m2m_changed(self, sender, instance, action, **kwargs):
        if action in ("post_add", "post_remove", "post_clear"):
            self.handle_save(sender, instance)



class CelerySignalProcessor(SignalProcessor):
    def handle_save(self, sender, instance, **kwargs):
        instance_pk = typesense_registry.get_model_pk(instance) or instance.pk
        self.save_task.apply_async((instance_pk,instance.__class__.__name__),countdown=5)

    def handle_delete(self, sender, instance, **kwargs):
        instance_pk = typesense_registry.get_model_pk(instance)
        self.delete_task.delay(instance_pk,instance.__class__.__name__)

    def handle_m2m_changed(self, sender, instance, action, **kwargs):
        if action in ("post_add", "post_remove", "post_clear"):
            self.handle_save(sender, instance)

    @shared_task()
    def save_task(pk,model_name):
        instance = None
        for model in typesense_registry.models:
            if model.__name__ == model_name:
                instance = model.objects.get(pk=pk)
                typesense_registry.update(instance)
        for model in typesense_registry.related_models:
            if model.__name__ == model_name:
                for document in typesense_registry.related_models[model]:
                    document_instance = document()
                    instance = model.objects.get(pk=pk)
                    related_for_update = document_instance.get_instances_from_related(instance)
                    for related_instance in related_for_update:
                        document_instance.update_document(related_instance)

    @shared_task()
    def delete_task(pk,model_name):
        typesense_registry.delete(pk,model_name)

    