# Typesense Django Simple

A simple Typesense integration for Django. Works like Django Elasticsearch DSL.

## Usage


### Creating documents

```python

# typesense_models.py

from typesense_documents.document import TypesenseDocument
from typesense_documents import fields
froom typesense_documents.registry import typesense_registry
from my_app.models import MyModel

@typesense_registry.register_model
class Document(TypesenseDocument):
    name = fields.StringField()
    class Meta: 
        model = MyModel
```

### Add application to INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    'typesense_documents',
    ...
]
```
### Add typesense configuration to settings.py

```python
# settings.py

TYPESENSE_HOST = "localhost"
TYPESENSE_PORT = 8108
TYPESENSE_PROTOCOL = "http"
TYPESENSE_API_KEY = "typesense_api_key"

### Use command for creating typesense collections

```bash
./manage.py build_index
```

### Text Search

```python    

results = Document().search(
    q="query",
    query_by="name",
    sort_by="name",
    per_page=50,
    page=1,
    filter_by="name",
)
```

### Image Search

```python    

image = "base64_image"
results = Document().search_by_image(
    vector_query = image
    embedding_field_name = "embedding",
    
)
