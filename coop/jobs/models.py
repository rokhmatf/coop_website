from django.db import models
from accounts.models import User

class Supervisor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supervisor_profile')
    nama = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    no_hp = models.CharField(max_length=15, blank=True, null=True)
    perusahaan = models.CharField(max_length=200, blank=True, null=True)
    bidang_usaha = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.nama} - {self.email} - {self.no_hp}"

    def get_mahasiswa_magang(self):
        """Get students supervised by this supervisor"""
        from coops.models import KonfirmasiMagang
        return KonfirmasiMagang.objects.filter(email_supervisor=self.email)