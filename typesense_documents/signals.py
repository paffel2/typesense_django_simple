from typesense_documents.registry import typesense_registry
from django.db import models


class SignalProcessor:
    def __init__(self):
        models.signals.post_save.connect(self.handle_save)
        models.signals.post_delete.connect(self.handle_delete)
        models.signals.m2m_changed.connect(self.handle_m2m_changed)

    def handle_save(self, sender, instance, **kwargs):
        typesense_registry.update(instance)

    def handle_delete(self, sender, instance, **kwargs):
        typesense_registry.delete(instance)

    def handle_m2m_changed(self, sender, instance, action, **kwargs):
        if action in ("post_add", "post_remove", "post_clear"):
            self.handle_save(sender, instance)
