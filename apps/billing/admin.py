from django.contrib import admin

from apps.billing.models import Payment, Plan, Subscription, SubscriptionContact


class SubscriptionContactInline(admin.TabularInline):
    model = SubscriptionContact
    extra = 0
    max_num = SubscriptionContact.MAX_CONTACTS


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("payment_date", "created_at", "updated_at")


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "billing_period", "is_active", "updated_at")
    list_filter = ("is_active", "billing_period")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "plan",
        "start_date",
        "end_date",
        "status",
        "auto_renew",
        "updated_at",
    )
    list_filter = ("status", "auto_renew", "plan")
    search_fields = ("company__name_short", "company__name_long")
    readonly_fields = ("integrity_signature", "created_at", "updated_at")
    inlines = (SubscriptionContactInline, PaymentInline)


@admin.register(SubscriptionContact)
class SubscriptionContactAdmin(admin.ModelAdmin):
    list_display = ("full_name", "subscription", "email", "phone", "role")
    search_fields = ("full_name", "email", "subscription__company__name_short")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("subscription", "amount", "method", "payment_date", "transaction_id")
    list_filter = ("method",)
    search_fields = ("transaction_id", "subscription__company__name_short")
    readonly_fields = ("payment_date", "created_at", "updated_at")
