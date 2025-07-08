from django.apps import AppConfig
from typesense_documents.signals import SignalProcessor
from django.utils.module_loading import autodiscover_modules


class TypesenseDocumentsConfig(AppConfig):
    name = "typesense_documents"
    signal_processor = None

    def ready(self):
        autodiscover_modules("typesense_models")
        self.signal_processor = SignalProcessor()
