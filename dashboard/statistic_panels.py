from wagtail.admin.ui.components import Component
from django.utils.translation import gettext_lazy as _
import redis
from redis.exceptions import TimeoutError


class ProvidersChart(Component):
    order = 900
    template_name = "statistics/providers_chart.html"

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)

        r = redis.Redis(
            host=settings.MQTT_REDIS_HOST,
            port=settings.MQTT_REDIS_PORT,
            db=settings.MQTT_REDIS_DB,
            socket_timeout=1,
        )

        providers_counter = {}
        try:
            for key in r.scan_iter(f"{settings.IPINFO_LITE_PREFIX}:*"):
                as_name = ""
                try:
                    msg = r.get(key.decode())
                    try:
                        msg_string = msg.decode()
                        msg_json = json.loads(msg_string)
                        try:
                            as_name = msg_json["as_name"]
                        except IndexError or KeyError:
                            pass

                    except AttributeError:
                        pass

                except TimeoutError:
                    pass

                try:
                    providers_counter[as_name] += 1
                except IndexError or KeyError:
                    providers_counter[as_name] = 1

        except TimeoutError:
            pass

        labels = []
        data = []
        chart_title = _("Providers Distribution")

        if providers_counter:
            for key, value in providers_counter.items():
                labels.append(key)
                data.append(value)

        context["data_providers"] = data
        context["labels_providers"] = labels
        context["chart_title_providers"] = chart_title

        return context
