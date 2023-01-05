from paho.mqtt import client as mqtt
from django.conf import settings


def on_publish(client, userdata, result):
    print('Message: {}'.format(userdata))


def mqtt_rcall_send(network_id, member_id, command):
    rcall_command = '!'.join([network_id, member_id, command])

    client = mqtt.Client()
    client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)
    client.on_publish = on_publish

    client.connect(settings.MQTT_HOST, int(settings.MQTT_PORT))

    result = client.publish('backone/rcall', rcall_command)

    return result
