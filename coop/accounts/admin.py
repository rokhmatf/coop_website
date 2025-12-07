from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Mahasiswa, Kaprodi

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
    list_display = ("nama", "nim", "jurusan", "prodi", "angkatan", "email", "no_hp")
    search_fields = ("nama__username", "nim", "email")
    list_filter = ("jurusan", "prodi", "angkatan")
    ordering = ("-angkatan", "nim")

admin.site.register(Mahasiswa, MahasiswaAdmin)

class KaprodiAdmin(admin.ModelAdmin):
    list_display = ("nama", "jurusan", "email", "no_hp")
    search_fields = ("nama", "email")
    list_filter = ("jurusan",)
    ordering = ("jurusan", "nama")

admin.site.register(Kaprodi, KaprodiAdmin)