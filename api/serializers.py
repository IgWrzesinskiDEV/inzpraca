from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import GodzinyPracy, WniosekUrlopowy, Profile
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import ROLE_CHOICES

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'dzial']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request', None)

        # When Swagger or unauthenticated access is generating the schema
        if request is None or getattr(request, 'swagger_fake_view', False):
            return fields

        user = getattr(request, 'user', None)

        # Check if user has 'role' attribute (not an AnonymousUser)
        if hasattr(user, 'role'):
            if user.role in ['kierownik', 'admin']:
                fields['username'].read_only = True
                fields['email'].read_only = True
                fields['role'].read_only = True
            elif user.role == 'pracownik':
                for field in fields.values():
                    field.read_only = True

        return fields


class GodzinyPracySerializer(serializers.ModelSerializer):
    czas_pracy = serializers.FloatField(read_only=True)

    class Meta:
        model = GodzinyPracy
        fields = '__all__'


class WniosekUrlopowySerializer(serializers.ModelSerializer):
    class Meta:
        model = WniosekUrlopowy
        fields = ['id', 'pracownik', 'wybrane_dni', 'status', 'data_utworzenia']
        read_only_fields = ['pracownik', 'status', 'data_utworzenia']


class ProfileSerializer(serializers.ModelSerializer):
    dzial = serializers.CharField(source='user.dzial', read_only=True)

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'birth_date', 'dzial']
        read_only_fields = ['dzial']


class CustomRegisterSerializer(RegisterSerializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    role = serializers.ChoiceField(choices=ROLE_CHOICES, default='pracownik')
    dzial = serializers.CharField(required=False, allow_blank=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['first_name'] = self.validated_data.get('first_name', '')
        data['last_name'] = self.validated_data.get('last_name', '')
        data['role'] = self.validated_data.get('role', 'pracownik')
        data['dzial'] = self.validated_data.get('dzial', '')
        return data
