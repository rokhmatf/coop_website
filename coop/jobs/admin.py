from django.contrib import admin
from .models import Supervisor

@admin.register(Supervisor)
class SupervisorAdmin(admin.ModelAdmin):
    list_display = ['nama', 'email', 'no_hp', 'perusahaan']
    search_fields = ['nama', 'email', 'perusahaan']
    list_filter = ['bidang_usaha']