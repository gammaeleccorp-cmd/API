from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from .validators import mobile_validator, national_id_format_validator, validate_national_id_checksum


class User(AbstractUser):
    """
    One account table for everybody who logs in:

    * role=user    -> registers with mobile + national_id + password, logs in with
                      username == mobile.
    * role=company -> created by staff in the admin panel, logs in with its own username.
    * staff / superuser accounts are used for the admin panel only (not for the API).
    """

    class Role(models.TextChoices):
        USER = "user", "User"
        COMPANY = "company", "Company"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    mobile = models.CharField(
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        validators=[mobile_validator],
    )
    national_id = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        validators=[national_id_format_validator, validate_national_id_checksum],
    )
    company_name = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(role="company")
                    | Q(is_staff=True)
                    | Q(mobile__isnull=False, national_id__isnull=False)
                ),
                name="regular_user_needs_mobile_and_national_id",
            ),
            models.CheckConstraint(
                condition=~Q(role="company") | ~Q(company_name=""),
                name="company_needs_name",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.role == self.Role.USER and not self.is_staff:
            if not self.mobile:
                errors["mobile"] = "Required for regular users."
            if not self.national_id:
                errors["national_id"] = "Required for regular users."
        if self.role == self.Role.COMPANY and not self.company_name:
            errors["company_name"] = "Required for companies."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # A regular user logs in with the mobile number, so username always mirrors it.
        if self.role == self.Role.USER and self.mobile:
            self.username = self.mobile
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Company(User):
    """Proxy model: lets the admin panel manage companies in their own section."""

    class Meta:
        proxy = True
        verbose_name = "company"
        verbose_name_plural = "companies"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Every Company instance is a company account, including new ones built by the admin form.
        self.role = User.Role.COMPANY