from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import Company, User

admin.site.site_header = "Rahban Administration"
admin.site.site_title = "Rahban Admin"


# The stock auth forms are bound to auth.User, so they must be re-pointed at the swapped model.
class UserCreationForm(AdminUserCreationForm):
    class Meta(AdminUserCreationForm.Meta):
        model = User


class UserChangeFormCustom(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """All accounts: regular users, companies and staff."""

    form = UserChangeFormCustom
    add_form = UserCreationForm
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Account", {"fields": ("role", "mobile", "national_id", "company_name")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Account", {"fields": ("role", "mobile", "national_id", "company_name")}),
    )
    list_display = ("username", "role", "mobile", "national_id", "company_name", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "mobile", "national_id", "company_name")
    ordering = ("id",)


@admin.register(Company)
class CompanyAdmin(DjangoUserAdmin):
    """Create and manage company accounts (replaces the old admin-only company endpoints)."""

    form = UserChangeFormCustom
    add_form = UserCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Company", {"fields": ("company_name", "is_active")}),
    )
    add_fieldsets = (
        DjangoUserAdmin.add_fieldsets[0],
        ("Company", {"fields": ("company_name",)}),
    )
    list_display = ("username", "company_name", "is_active", "date_joined")
    list_filter = ("is_active",)
    search_fields = ("username", "company_name")
    ordering = ("id",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role=User.Role.COMPANY)

    def save_model(self, request, obj, form, change):
        obj.role = User.Role.COMPANY
        super().save_model(request, obj, form, change)
