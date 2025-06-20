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
            "is_dpi",
            "online_at",
            "offline_at",
            "mobile_number_first",
            "mqtt",
            "quota_first",
            "quota_first_prev",
        ]
        read_only_fields = ["__all__"]
