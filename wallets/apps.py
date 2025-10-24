from django.apps import AppConfig


class WalletsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wallets"

    def ready(self):
        """Import signals when app is ready."""
        import wallets.signals  # Register wallet auto-creation signals
