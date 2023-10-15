class HeadscaleRouter:

    route_app_labels = {"headscale"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "headscale"
        return None

    def db_for_write(self, model, **hints):
        """
        Writes always go to default.
        """
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return False
        return True
