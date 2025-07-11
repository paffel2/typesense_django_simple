from django.apps import AppConfig
from typesense_documents.signals import SignalProcessor,CelerySignalProcessor
from django.utils.module_loading import autodiscover_modules
from django.conf import settings

class TypesenseDocumentsConfig(AppConfig):
    name = "typesense_documents"
    signal_processor = None

    def ready(self):
        autodiscover_modules("typesense_models")
        if settings.TYPESENSE_PROCESSOR_TYPE == "celery":
            self.signal_processor = CelerySignalProcessor()
        else:
            self.signal_processor = SignalProcessor()
