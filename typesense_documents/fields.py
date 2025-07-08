from typing import Optional, List
import base64
from PIL import Image
from io import BytesIO


class BaseField:
    field_type = None
    field_python_type = None

    def __init__(
        self,
        value: Optional[str] = None,
        sort: bool = False,
        index: bool = True,
        optional: bool = False,
        store: bool = True,
        locale: str = "",
        stem: bool = False,
    ):

        self.value = value
        self.sort = sort
        self.index = index
        self.optional = optional
        self.locale = locale or "en"
        self.stem = stem
        self.store = store

    def get_field_schema(self):
        return {
            "type": self.field_type,
            "locale": self.locale,
            "sort": self.sort,
            "stem": self.stem,
            "store": self.store,
            "index": self.index,
            "optional": self.optional,
        }

    def prepare_value(self, attr):
        if isinstance(attr, self.field_python_type) or (self.optional and attr is None):
            return attr
        else:
            return self.field_python_type(attr)


class Int32(BaseField):
    field_type = "int32"
    field_python_type = int


class StringField(BaseField):
    field_type = "string"
    field_python_type = str

    def __init__(
        self,
        value=None,
        sort=False,
        index=True,
        optional=False,
        store=True,
        locale="en",
        stem=False,
        token_separators: List[str] = [],
    ):
        super().__init__(value, sort, index, optional, store, locale, stem)
        self.token_separators = token_separators

    def get_field_schema(self):
        schema = super().get_field_schema()
        schema["token_separators"] = self.token_separators
        return schema


class BooleanField(BaseField):
    field_type = "bool"
    field_python_type = bool


class EmbeddingField(BaseField):
    def __init__(self, index=True, optional=False, store=True, model_name="", from_field=None):

        self.index = index
        self.optional = optional
        self.store = store
        self.model_name = model_name
        self.from_field = from_field

    def get_field_schema(self):
        return {
            "type": "float[]",
            "embed": {
                "from": [self.from_field],
                "model_config": {
                    "model_name": self.model_name,
                },
            },
        }


class ImageField(BaseField):
    field_type = "image"

    def __init__(
        self,
        value: Optional[str] = None,
        index=False,
        optional=False,
        store=False,
    ):
        self.value = value
        self.index = index
        self.optional = optional
        self.store = store

    def get_field_schema(self):
        return {"type": "image", "store": self.store, "index": self.index, "optional": self.optional}

    def prepare_value(self, attr):
        try:
            file = attr.open("rb")
            pill_image = Image.open(file)
            if pill_image.mode in ("RGBA", "P"):
                pill_image = pill_image.convert("RGB")
            output_buffer = BytesIO()
            pill_image.save(output_buffer, format="JPEG", quality=100)
            output_buffer.seek(0)
            b64_image = base64.b64encode(output_buffer.getvalue()).decode("utf-8")
            return b64_image
        except Exception:
            return None
