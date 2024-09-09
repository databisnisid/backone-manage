from rest_framework import serializers
from .models import Members
from mqtt.serializers import MqttSerializers


class MembersSerializers(serializers.ModelSerializer):
    mqtt = MqttSerializers()

    class Meta:
        model = Members
        fields = ('name', 'member_code', 'description',
                  'member_id', 'address', 'location',
                  'online_at', 'offline_at', 'mobile_number_first'
                  )
