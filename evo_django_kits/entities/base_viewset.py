from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser

from evo_django_kits.entities.evo_response import EvoResponse
from evo_django_kits.entities.serializers.bulk_delete_serializer import BulkDeleteSerializer


class BaseViewSet(viewsets.ModelViewSet):
    response = EvoResponse

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"user": self.request.user})
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return self.response(
            data=serializer.data,
            status=201,
            message="Created Successfully",
            headers=headers,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.response(data=serializer.data, status=200, message="Updated Successfully")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.response(status=204, message="Deleted Successfully")

    @action(
        detail=False,
        methods=["DELETE"],
        url_name="bulk-delete",
        serializer_class=BulkDeleteSerializer,
        permission_classes=[IsAdminUser],
    )
    def bulk_delete(self, request):
        """
        For each list end point have endpoint to bulk delete with param ids
        example: /users/bulk_delete/?ids=21,22
        """
        ids = request.query_params.get("ids", None)
        ids = [int(_id) for _id in ids.split(",")] if ids else []
        data = {"ids": ids}
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["ids"]
        self.queryset.filter(id__in=ids).delete()
        return self.response(status=204, data=[ids], message=f"Delete {len(ids)} successful")
