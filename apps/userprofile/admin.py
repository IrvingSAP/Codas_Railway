from django.contrib import admin

from apps.userprofile.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company",
        "user_type",
        "status",
        "email_confirmed",
        "tfa_verified",
        "created_at",
    )
    list_filter = ("user_type", "status", "email_confirmed", "tfa_verified")
    search_fields = ("user__username", "user__email", "document_id")
    ordering = ("user__username",)
    autocomplete_fields = ("user", "company", "created_by", "updated_by")
    readonly_fields = (
        "created_at",
        "updated_at",
        "totp_secret",
        "email_confirm_code",
        "email_confirm_exp",
    )
