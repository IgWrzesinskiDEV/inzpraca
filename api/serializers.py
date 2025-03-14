from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import GodzinyPracy, WniosekUrlopowy

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'dzial']

class GodzinyPracySerializer(serializers.ModelSerializer):
    czas_pracy = serializers.FloatField(read_only=True)

    class Meta:
        model = GodzinyPracy
        fields = '__all__'

class WniosekUrlopowySerializer(serializers.ModelSerializer):
    class Meta:
        model = WniosekUrlopowy
        fields = '__all__'
