class MqttRouter:

    route_app_labels = {"mqtt"}

    def db_for_read(self, model, **hints):
        if model._meta.label_lower in self.route_app_labels:
            print(model._meta.label_lower)
            return "default_ramdisk"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.label_lower in self.route_app_labels:
            print(model._meta.label_lower)
            return "default_ramdisk"
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            print(app_label)
            return db == "default_ramdisk"
        return None
