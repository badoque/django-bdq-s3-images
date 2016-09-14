from rest_framework import serializers
from image_management.models import ExternalImage

class ExternalImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    name = serializers.SerializerMethodField()
    extension = serializers.SerializerMethodField()

    class Meta:
        model = ExternalImage
        fields = ('id', 'url', 'type', 'size', 'name', 'extension')

    def get_name(self, obj):
        return obj.url.split('/')[-1]

    def get_extension(self, obj):
        return obj.url.split('.')[-1]

    def create(self, validated_data):
        return ExternalImage.objects.create(**validated_data)