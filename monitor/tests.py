from django.test import TestCase

from monitor.utils import (
    compare_values,
    is_problem_cpu,
    is_problem_memory,
    is_problem_packet_loss,
    is_problem_round_trip,
    is_problem_quota_first_gb,
    is_problem_quota_first_day,
)


class FakeMqtt:
    """Stand-in exposing the accessors monitor/utils.py consumes."""

    def __init__(self, cpu=(0, 0, 0), memory=0.0, packet_loss=0.0, round_trip=0.0, quota=(0, 0, 0, ""), quota_prev=(0, 0, 0, "")):
        self._cpu = cpu
        self.memory_usage = memory
        self._packet_loss = packet_loss
        self._round_trip = round_trip
        self._quota = quota
        self._quota_prev = quota_prev

    def get_cpu_usage(self):
        return self._cpu

    def get_packet_loss(self):
        return self._packet_loss

    def get_round_trip(self):
        return self._round_trip

    def get_quota_first(self):
        return self._quota

    def get_quota_first_prev(self):
        return self._quota_prev


class CompareValuesTests(TestCase):
    def test_greater_is_true(self):
        self.assertTrue(compare_values(5, 3))

    def test_equal_is_false(self):
        self.assertFalse(compare_values(5, 5))

    def test_lesser_is_false(self):
        self.assertFalse(compare_values(3, 5))


class ThresholdTests(TestCase):
    """V4 (threshold logic reading telemetry): each metric flags a problem only
    when its value exceeds the threshold."""

    def test_cpu_over_threshold(self):
        self.assertTrue(is_problem_cpu(FakeMqtt(cpu=(1, 80, 2)), 50))

    def test_cpu_under_threshold(self):
        self.assertFalse(is_problem_cpu(FakeMqtt(cpu=(1, 20, 2)), 50))

    def test_memory_over_threshold(self):
        self.assertTrue(is_problem_memory(FakeMqtt(memory=90.0), 75))

    def test_memory_under_threshold(self):
        self.assertFalse(is_problem_memory(FakeMqtt(memory=50.0), 75))

    def test_packet_loss_over_threshold(self):
        self.assertTrue(is_problem_packet_loss(FakeMqtt(packet_loss=40.0), 10))

    def test_round_trip_over_threshold(self):
        self.assertTrue(is_problem_round_trip(FakeMqtt(round_trip=500.0), 200))

    def test_quota_gb_empty_total_false(self):
        # quota_total 0 -> returns False, not crash
        self.assertFalse(is_problem_quota_first_gb(FakeMqtt(quota=(0, 0, 0, "")), 100))

    def test_quota_day_empty_total_false(self):
        self.assertFalse(is_problem_quota_first_day(FakeMqtt(quota=(0, 0, 0, "")), 100))
