import importlib

from django.conf import settings
from rest_framework import serializers
from .evo_router import get_router


class RestFrameworkModuler:
    """Class that handles registration of Django models with REST framework"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RestFrameworkModuler, cls).__new__(cls)
            # Initialize instance attributes
            cls._instance.router = get_router()
            cls._instance._registry = {}
        return cls._instance

    def create_serializer_class(self, model_class, **options):
        """Dynamically create a serializer class for a model"""
        # Define Meta class attributes
        meta_attrs = {"model": model_class, "fields": []}

        # Process fields
        all_fields = options.get("fields", "__all__")
        nested_fields = {}
        transformed_field_names = []

        # If fields is not "__all__", process for nested lookups
        if all_fields != "__all__":
            regular_fields = []
            for field in all_fields:
                if "." in field:
                    # This is a nested field
                    parts = field.split(".", 1)
                    base_field, nested_attr = parts
                    if base_field not in nested_fields:
                        nested_fields[base_field] = []
                    nested_fields[base_field].append(nested_attr)

                    # Ensure the base field is included
                    if base_field not in regular_fields:
                        regular_fields.append(base_field)

                    # Store the transformed field name
                    transformed_field_names.append(field.replace(".", "__"))
                else:
                    regular_fields.append(field)

            # Include both regular fields and transformed nested fields in Meta.fields
            meta_attrs["fields"] = regular_fields + transformed_field_names
        else:
            meta_attrs["fields"] = "__all__"

        # Handle read_only_fields if specified
        if "read_only_fields" in options:
            meta_attrs["read_only_fields"] = options.get("read_only_fields")

        # Create Meta class
        Meta = type("Meta", (), meta_attrs)

        # Initialize serializer attributes with Meta class
        serializer_attrs = {"Meta": Meta}

        # Add any custom serializer fields
        serializer_attrs.update(options.get("serializer_fields", {}))

        # Add method fields for nested attributes
        for base_field, attrs in nested_fields.items():
            for attr in attrs:
                original_field_name = f"{base_field}.{attr}"
                # Create a valid Python identifier for the serializer field using double underscores
                safe_field_name = original_field_name.replace(".", "__")
                method_name = f"get_{safe_field_name}"

                # Create the getter method with a closure that properly captures variables
                def make_getter(base_field, attr):
                    def getter(self, obj):
                        # Navigate through the object relationship
                        related_obj = getattr(obj, base_field, None)
                        if related_obj is None:
                            return None
                        return getattr(related_obj, attr, None)

                    return getter

                # Add the method to the serializer
                serializer_attrs[method_name] = make_getter(base_field, attr)
                # Add the SerializerMethodField with the safe name
                serializer_attrs[safe_field_name] = serializers.SerializerMethodField(method_name=method_name)

        # Create and return the serializer class
        return type(f"{model_class.__name__}Serializer", (serializers.ModelSerializer,), serializer_attrs)

    def create_viewset_class(self, model_class, serializer_class, abstract_viewset_class=None, mixins=None, **options):
        """Dynamically create a viewset class for a model"""

        if abstract_viewset_class is None:
            # get EVO_ABSTRACT_VIEWSET from settings
            # if not set, use BaseViewSet
            if not hasattr(settings, "EVO_ABSTRACT_VIEWSET"):
                from evo_django_kits.entities.base_viewset import BaseViewSet

                abstract_viewset_class = BaseViewSet
            else:
                # abstract_viewset_class is a string, import it
                # ex: "evo_django_kits.entities.base_viewset:BaseViewSet"
                abstract_viewset_class = importlib.import_module(settings.EVO_ABSTRACT_VIEWSET)
        if mixins is None:
            mixins = []

        class DynamicViewSet(abstract_viewset_class, *mixins):
            pass

        # Set basic attributes
        viewset_attrs = {
            "queryset": model_class.objects.all(),
            "serializer_class": serializer_class,
        }

        # Add optional attributes
        search_fields = options.get("search_fields")
        if search_fields:
            viewset_attrs["search_fields"] = search_fields

        ordering_fields = options.get("ordering_fields")
        if ordering_fields:
            viewset_attrs["ordering_fields"] = ordering_fields

        ordering = options.get("ordering")
        if ordering:
            viewset_attrs["ordering"] = ordering

        # Add filter fields
        filter_fields = options.get("filterset_fields")
        if filter_fields:
            viewset_attrs["filterset_fields"] = filter_fields

        # Create the viewset class
        viewset_class = type(f"{model_class.__name__}ViewSet", (DynamicViewSet,), viewset_attrs)

        return viewset_class

    def get_resource_name(self, model_class):
        """
        Convert model class name to URL resource name
        Example: University -> universities
        """
        model_name = model_class.__name__

        # CamelCase to kebab-case with pluralization
        chars = []
        for i, char in enumerate(model_name):
            if i > 0 and char.isupper():
                chars.append("-")
            chars.append(char.lower())

        # Simple pluralization
        name = "".join(chars)
        if name.endswith("y"):
            return f"{name[:-1]}ies"
        else:
            return f"{name}s"

    def register_model(self, model_class, abstract_viewset_class=None, mixins=None, **options):
        """
        Register a model with the REST framework.

        Args:
            model_class: The Django model class to register
            **options: Additional options for customization
                - fields: Fields to include in the serializer (default: '__all__')
                - serializer_fields: Custom serializer fields
                - search_fields: Fields to search on
                - ordering_fields: Fields to allow ordering on
                - ordering: Default ordering
                - resource_name: Custom URL resource name
                - serializer_class: Custom serializer class (if not auto-creating)
                - viewset_class: Custom viewset class (if not auto-creating)

        Returns:
            The registered viewset class
        """
        # Check if model is already registered
        if model_class in self._registry:
            return self._registry[model_class]["viewset_class"]

        # Use custom serializer class or create one
        serializer_class = options.get("serializer_class")
        if serializer_class is None:
            serializer_class = self.create_serializer_class(model_class, **options)

        # Use custom viewset class or create one
        viewset_class = options.get("viewset_class")
        if viewset_class is None:
            print(f"Creating viewset class for {model_class.__name__}, options: {options}")
            viewset_class = self.create_viewset_class(
                model_class, serializer_class, abstract_viewset_class=abstract_viewset_class, mixins=mixins, **options
            )

        # Get resource name for URL
        resource_name = options.get("resource_name")
        if resource_name is None:
            resource_name = self.get_resource_name(model_class)

        # Register viewset with router
        self.router.register(resource_name, viewset_class, basename=resource_name)

        # Store in registry
        self._registry[model_class] = {
            "serializer_class": serializer_class,
            "viewset_class": viewset_class,
            "resource_name": resource_name,
            "options": options,
        }

        return viewset_class

    def unregister_model(self, model_class):
        """Unregister a model from the REST framework"""
        if model_class in self._registry:
            # Can't directly unregister from DefaultRouter, but we can keep track
            # of which models are registered
            del self._registry[model_class]
            return True
        return False

    def is_registered(self, model_class):
        """Check if a model is registered"""
        return model_class in self._registry


def register_model(model_class, abstract_viewset_class=None, mixins=None, **options):
    RestFrameworkModuler().register_model(
        model_class, abstract_viewset_class=abstract_viewset_class, mixins=mixins, **options
    )


# Decorator for registering models
def rest_api(resource_name=None, abstract_viewset_class=None, mixins=None, **options):
    """
    Decorator for registering models with the REST framework

    @rest_api(
        fields=['name', 'id'],
        search_fields=['name'],
        ordering_fields=['name', 'id'],
        filterset_fields=['name', 'id', 'related__field'],
        read_only_fields=['id']
    )
    class MyModel(models.Model):
        ...
    """

    def _model_wrapper(model_class):
        if resource_name:
            options["resource_name"] = resource_name
        register_model(model_class, abstract_viewset_class=abstract_viewset_class, mixins=mixins, **options)
        return model_class

    return _model_wrapper
