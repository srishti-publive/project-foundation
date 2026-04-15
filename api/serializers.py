from rest_framework import serializers
from .models import Task, WebhookSubscription
from .recurrence import is_valid_recurrence_rule


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"

    def validate_recurrence_rule(self, value):
        if value and not is_valid_recurrence_rule(value):
            raise serializers.ValidationError(
                "Must be a valid 5-field cron expression (e.g. '*/5 * * * *') "
                "or an ISO 8601 recurrence interval (e.g. 'R/PT1H', 'R/P1D')."
            )
        return value


class WebhookSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookSubscription
        # secret is intentionally excluded; it is returned once in the view response.
        fields = ["id", "user_id", "url", "created_at"]
        read_only_fields = ["id", "created_at"]