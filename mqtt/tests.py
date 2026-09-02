from django.test import TestCase
from mqtt.models import Mqtt


class MqttSaveGuardTests(TestCase):
    """V7 / V4: Mqtt.save() must not raise IndexError on malformed telemetry strings."""

    def test_malformed_packet_loss_no_crash(self):
        m = Mqtt(
            member_id="abcdefghij",
            packet_loss_string="10",  # only 1 comma-part, was [2] -> IndexError
        )
        m.save()  # must not raise
        m.refresh_from_db()
        self.assertEqual(m.packet_loss, 0)

    def test_malformed_round_trip_no_crash(self):
        m = Mqtt(
            member_id="abcdefghij",
            round_trip_string="nodash",  # split('=') -> 1 part, was [1] -> IndexError
        )
        m.save()
        m.refresh_from_db()
        self.assertEqual(m.round_trip, 0)

    def test_wellformed_values_populated(self):
        m = Mqtt(
            member_id="abcdefghij",
            packet_loss_string="1,2,3%,4",
            round_trip_string="abc=5/6",
        )
        m.save()
        m.refresh_from_db()
        self.assertEqual(m.packet_loss, 3.0)
        self.assertEqual(m.round_trip, 6.0)
