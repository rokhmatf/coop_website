from django.db import models
from accounts.models import User
from django.utils import timezone

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


class JobPosting(models.Model):
    """Model untuk lowongan pekerjaan/magang"""
    JOB_TYPE_CHOICES = [
        ('internship', 'Magang'),
        ('fulltime', 'Full Time'),
        ('parttime', 'Part Time'),
        ('contract', 'Kontrak'),
    ]

    title = models.CharField(max_length=200, verbose_name="Judul Lowongan")
    company_name = models.CharField(max_length=200, verbose_name="Nama Perusahaan")
    company_logo = models.URLField(blank=True, null=True, verbose_name="Logo Perusahaan (Firebase URL)")
    description = models.TextField(verbose_name="Deskripsi Pekerjaan")
    requirements = models.TextField(verbose_name="Persyaratan")
    location = models.CharField(max_length=200, verbose_name="Lokasi")
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='internship', verbose_name="Tipe Pekerjaan")
    salary_range = models.CharField(max_length=100, blank=True, null=True, verbose_name="Range Gaji")
    application_deadline = models.DateField(verbose_name="Batas Akhir Pendaftaran")
    posted_date = models.DateTimeField(default=timezone.now, verbose_name="Tanggal Posting")
    is_active = models.BooleanField(default=True, verbose_name="Status Aktif")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='job_postings', verbose_name="Dibuat Oleh")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-posted_date']
        verbose_name = "Lowongan Pekerjaan"
        verbose_name_plural = "Lowongan Pekerjaan"

    def __str__(self):
        return f"{self.title} - {self.company_name}"

    @property
    def is_expired(self):
        """Check if job posting has expired"""
        return timezone.now().date() > self.application_deadline

    @property
    def days_until_deadline(self):
        """Calculate days until application deadline"""
        delta = self.application_deadline - timezone.now().date()
        return delta.days


class JobApplication(models.Model):
    """Model untuk aplikasi lowongan oleh mahasiswa"""
    STATUS_CHOICES = [
        ('applied', 'Diajukan'),
        ('reviewed', 'Direview'),
        ('interview', 'Interview'),
        ('accepted', 'Diterima'),
        ('rejected', 'Ditolak'),
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications', verbose_name="Lowongan")
    mahasiswa = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications', limit_choices_to={'role': 'mahasiswa'}, verbose_name="Mahasiswa")
    cv_url = models.URLField(verbose_name="CV (Firebase URL)")
    cover_letter = models.TextField(verbose_name="Cover Letter", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied', verbose_name="Status")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan dari Admin/HR")
    applied_date = models.DateTimeField(default=timezone.now, verbose_name="Tanggal Apply")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_date']
        unique_together = ['job', 'mahasiswa']
        verbose_name = "Aplikasi Lowongan"
        verbose_name_plural = "Aplikasi Lowongan"

    def __str__(self):
        return f"{self.mahasiswa.get_full_name()} - {self.job.title}"