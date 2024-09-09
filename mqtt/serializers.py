from rest_framework import serializers
from .models import Mqtt


class MqttSerializers(serializers.ModelSerializer):
    class Meta:
        model = Mqtt
        fields = ('hostname', 'uptime')

