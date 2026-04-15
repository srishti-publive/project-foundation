from rest_framework import serializers
from .models import Task, WebhookSubscription


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"


class WebhookSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookSubscription
        # secret is intentionally excluded; it is returned once in the view response.
        fields = ["id", "user_id", "url", "created_at"]
        read_only_fields = ["id", "created_at"]