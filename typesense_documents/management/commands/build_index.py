from django.core.management.base import BaseCommand
from typesense_documents.registry import typesense_registry


class Command(BaseCommand):
    help = "Create typesense collections and fill"

    def add_arguments(self, parser):
        parser.add_argument("--use-batch", action="store_true",help="Use batches for update")

    def handle(self, *args, **options):
        use_batch = False
        if options["use-batch"]:
            use_batch = True
        for document in typesense_registry.index:
            document().init_collection(use_batch=use_batch)
