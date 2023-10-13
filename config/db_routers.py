class HeadscaleRouter:

    route_app_labels = {"headscale"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "headscale"
        return None

