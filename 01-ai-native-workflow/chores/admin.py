from django.contrib import admin

from .models import Assignment, Chore, CompletionEvent, Household, Membership


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "invite_code", "created_at")
    readonly_fields = ("invite_code", "created_at")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "household", "joined_at")
    list_filter = ("household",)


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ("title", "household", "points", "is_active", "created_at")
    list_filter = ("household", "is_active")
    search_fields = ("title", "description")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("chore", "assignee", "due_date", "status", "completed_at")
    list_filter = ("status", "due_date")
    date_hierarchy = "due_date"


@admin.register(CompletionEvent)
class CompletionEventAdmin(admin.ModelAdmin):
    list_display = ("assignment", "completed_by", "completed_at", "points_awarded")
    list_filter = ("completed_by",)
    readonly_fields = ("completed_at",)
