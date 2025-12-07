from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Mahasiswa

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("username", "email", "first_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("username", "email", "password", "role")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "role", "is_staff", "is_active")}
        ),
    )
    search_fields = ("username", "email")
    ordering = ("username",)

admin.site.register(User, CustomUserAdmin)

class MahasiswaAdmin(admin.ModelAdmin):
    list_display = ("nama", "nim", "prodi", "angkatan", "email", "no_hp")
    search_fields = ("nama__username", "nim", "email")
    list_filter = ("prodi", "angkatan")
    ordering = ("-angkatan", "nim")

admin.site.register(Mahasiswa, MahasiswaAdmin)