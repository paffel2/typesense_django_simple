from django.core.management.base import BaseCommand
from typesense_documents.registry import typesense_registry


class Command(BaseCommand):
    help = "Create typesense collections and fill"

    def handle(self, *args, **options):
        for document in typesense_registry.index:
            document().init_collection()
