from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "api"

    def ready(self) -> None:
        # Validate all plugins that exist right now so that a missing or
        # malformed handle() function is caught at startup, not at dispatch time.
        from .plugins import validate_all_plugins  # noqa: PLC0415
        validate_all_plugins()
