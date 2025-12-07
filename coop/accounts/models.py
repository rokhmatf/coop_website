from django.contrib.auth.models import AbstractUser
from django.db import models

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
    nama = models.CharField(max_length=100)
    nim = models.CharField(max_length=20)
    prodi = models.CharField(max_length=100)
    angkatan = models.IntegerField()
    jenis_kelamin = models.CharField(max_length=10, choices=[('L', 'Laki-laki'), ('P', 'Perempuan')])
    email = models.OneToOneField(User, on_delete=models.CASCADE)
    no_hp = models.CharField(max_length=15)
    konsultasi = models.CharField(max_length=100, blank=True, null=True)
    sptjm = models.CharField(max_length=100, blank=True, null=True)
    magang = models.BooleanField(default=False)
    porto = models.CharField(max_length=100, blank=True, null=True)
    cv = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.nama} {self.nim} {self.prodi} {self.angkatan} {self.jenis_kelamin} {self.email} {self.no_hp} {self.konsultasi} {self.sptjm} {self.porto} {self.cv}"
