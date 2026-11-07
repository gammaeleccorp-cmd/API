from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .validators import validate_national_id_checksum

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """Registration takes only mobile, national_id and password (username becomes the mobile)."""

    mobile = serializers.RegexField(r"^09[0-9]{9}$", max_length=11)
    national_id = serializers.RegexField(
        r"^[0-9]{10}$", max_length=10, validators=[validate_national_id_checksum]
    )
    password = serializers.CharField(max_length=128, write_only=True, validators=[validate_password])


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "role", "mobile", "national_id", "company_name", "date_joined"]
        read_only_fields = fields


class LoginSerializer(TokenObtainPairSerializer):
    """username (= mobile for regular users) + password -> access/refresh tokens + role."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.is_staff or self.user.is_superuser:
            # Same message as a wrong password, so API clients cannot probe for staff accounts.
            raise AuthenticationFailed("No active account found with the given credentials")
        data["role"] = self.user.role
        data["access_token"] = data["access"]  # Swagger UI reads this key
        data["token_type"] = "Bearer"
        return data


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    role = serializers.CharField()
    access_token = serializers.CharField()
    token_type = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
