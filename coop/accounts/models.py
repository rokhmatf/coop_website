from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('mahasiswa', 'Mahasiswa'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    @property
    def supervisor(self):
        """Get supervisor profile if user is a supervisor"""
        if self.role == 'supervisor':
            from jobs.models import Supervisor
            try:
                return self.supervisor_profile
            except:
                # Create supervisor profile if doesn't exist
                supervisor = Supervisor.objects.create(
                    user=self,
                    nama=self.get_full_name() or self.username,
                    email=self.email
                )
                return supervisor
        return None


class Mahasiswa(models.Model):
    nama = models.CharField(max_length=100, verbose_name="Nama Lengkap")
    nim = models.CharField(max_length=20, unique=True, verbose_name="NIM")
    prodi = models.CharField(max_length=100, verbose_name="Program Studi")
    angkatan = models.IntegerField(verbose_name="Tahun Angkatan")
    jenis_kelamin = models.CharField(max_length=10, choices=[('L', 'Laki-laki'), ('P', 'Perempuan')], verbose_name="Jenis Kelamin")
    email = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="User Account")
    no_hp = models.CharField(max_length=15, verbose_name="Nomor HP")

    # Firebase Storage URLs for documents
    konsultasi = models.URLField(max_length=500, blank=True, null=True, verbose_name="Bukti Konsultasi Mentor (URL)")
    sptjm = models.URLField(max_length=500, blank=True, null=True, verbose_name="Bukti SPTJM (URL)")
    cv = models.URLField(max_length=500, blank=True, null=True, verbose_name="CV (URL)")
    porto = models.URLField(max_length=500, blank=True, null=True, verbose_name="Portofolio (URL)")

    magang = models.BooleanField(default=False, verbose_name="Sudah Magang")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mahasiswa"
        verbose_name_plural = "Mahasiswa"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nama} - {self.nim}"

    @property
    def profile_completion(self):
        """Calculate profile completion percentage"""
        fields = [self.cv, self.porto, self.konsultasi, self.sptjm]
        completed = sum(1 for field in fields if field)
        return int((completed / len(fields)) * 100)
