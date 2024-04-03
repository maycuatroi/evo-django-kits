from rest_framework import serializers


class BulkDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), required=True)

    def validate(self, attrs):
        if not attrs["ids"]:
            raise serializers.ValidationError("ids is required")
        return attrs
