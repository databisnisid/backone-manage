from rest_framework import serializers
from .models import Members
from mqtt.serializers import MqttSerializers


class MembersSerializers(serializers.ModelSerializer):
    mqtt = MqttSerializers()

    class Meta:
        model = Members
        fields = [
            "name",
            "member_code",
            "description",
            "member_id",
            "address",
            "location",
            "is_authorized",
            "online_at",
            "offline_at",
            "mobile_number_first",
            "mqtt",
        ]
        read_only_fields = ["__all__"]
