from django.db import models
from accounts.models import User
from django.utils import timezone

class KonfirmasiMagang(models.Model):
    mahasiswa = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'mahasiswa'})
    periode_awal = models.DateField(default=None, null=True, blank=True)
    periode_akhir = models.DateField(default=None, null=True, blank=True)
    posisi = models.CharField(max_length=200)
    nama_perusahaan = models.CharField(max_length=200)
    alamat_perusahaan = models.TextField()
    bidang_usaha = models.CharField(max_length=200)
    nama_supervisor = models.CharField(max_length=200)
    email_supervisor = models.EmailField()
    wa_supervisor = models.CharField(max_length=20, blank=True, null=True)
    supervisor_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_magang', limit_choices_to={'role': 'supervisor'}, verbose_name="Supervisor Account")
    surat_penerimaan = models.URLField(max_length=500, verbose_name="Surat Penerimaan (Firebase URL)")

    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ], default='pending')

    # optional deadline for when the student must have secured a placement
    deadline = models.DateField(null=True, blank=True)

    # whether this mahasiswa is required to submit weekly reports
    requires_weekly_report = models.BooleanField(default=False)

    # last time a reminder email was sent
    last_reminder_sent = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.mahasiswa.username} - {self.nama_perusahaan}"


class EvaluasiTemplate(models.Model):
    """Template evaluasi yang dibuat oleh admin untuk UTS/UAS"""
    nama = models.CharField(max_length=200)
    jenis = models.CharField(max_length=20, choices=[
        ('uts', 'UTS - Laporan Kemajuan'),
        ('uas', 'UAS - Laporan Akhir'),
    ])
    pertanyaan = models.JSONField(help_text="Array of questions for the evaluation")
    aktif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    periode_mulai = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Periode Mulai',
        help_text='Tanggal dan waktu mulai periode pengisian evaluasi'
    )
    periode_selesai = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Periode Selesai',
        help_text='Tanggal dan waktu akhir periode pengisian evaluasi'
    )
    auto_distribute = models.BooleanField(
        default=False,
        verbose_name='Auto Distribute',
        help_text='Otomatis distribute evaluasi ke supervisor saat periode dimulai'
    )

    def __str__(self):
        return f"{self.nama} ({self.get_jenis_display()})"

    def is_period_active(self):
        """Check if evaluation period is currently active"""
        if not self.periode_mulai or not self.periode_selesai:
            return True
        now = timezone.now()
        return self.periode_mulai <= now <= self.periode_selesai

    def period_status(self):
        """Get current period status: 'not_started', 'active', 'ended', or 'no_period'"""
        if not self.periode_mulai or not self.periode_selesai:
            return 'no_period'
        now = timezone.now()
        if now < self.periode_mulai:
            return 'not_started'
        elif now > self.periode_selesai:
            return 'ended'
        else:
            return 'active'

    def period_status_display(self):
        """Get human-readable period status"""
        status = self.period_status()
        status_map = {
            'no_period': 'Tidak ada batasan periode',
            'not_started': 'Belum dimulai',
            'active': 'Aktif',
            'ended': 'Sudah berakhir'
        }
        return status_map.get(status, 'Unknown')

    def can_be_filled(self):
        """Check if evaluation can be filled by supervisor"""
        if not self.aktif:
            return False
        return self.is_period_active()


class EvaluasiSupervisor(models.Model):
    """Evaluasi yang diisi oleh supervisor"""
    konfirmasi = models.ForeignKey(KonfirmasiMagang, on_delete=models.CASCADE)
    template = models.ForeignKey(EvaluasiTemplate, on_delete=models.CASCADE)
    jawaban = models.JSONField(help_text="Answers corresponding to template questions", default=dict, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Belum Diisi'),
        ('completed', 'Sudah Diisi'),
        ('finished', 'Selesai'),
    ], default='pending')
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['konfirmasi', 'template']

    def __str__(self):
        return f"Evaluasi {self.template.nama} - {self.konfirmasi.mahasiswa.username}"


class LaporanKemajuan(models.Model):
    """Laporan kemajuan bulanan yang diisi mahasiswa"""
    konfirmasi = models.ForeignKey(KonfirmasiMagang, on_delete=models.CASCADE, related_name='laporan_kemajuan')
    bulan = models.DateField()
    
    # Informasi yang diminta dalam requirement
    profil_perusahaan = models.TextField(help_text="Profil perusahaan")
    jobdesk = models.TextField(help_text="Jobdesk yang dikerjakan")
    suasana_lingkungan = models.TextField(help_text="Suasana lingkungan pekerjaan")
    manfaat_perkuliahan = models.TextField(help_text="Apa yang didapatkan dari perkuliahan yang berguna untuk pekerjaan")
    kebutuhan_pembelajaran = models.TextField(help_text="Apa yang berguna pada perusahaan tapi belum didapatkan dalam pembelajaran")
    
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
    ], default='draft')
    
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['konfirmasi', 'bulan']

    def __str__(self):
        return f"Laporan {self.bulan.strftime('%B %Y')} - {self.konfirmasi.mahasiswa.username}"


class LaporanAkhir(models.Model):
    """Laporan akhir yang dikumpulkan mahasiswa di akhir magang"""
    konfirmasi = models.OneToOneField(KonfirmasiMagang, on_delete=models.CASCADE, related_name='laporan_akhir')
    
    # Konten laporan akhir
    ringkasan_kegiatan = models.TextField(help_text="Ringkasan kegiatan selama magang")
    pencapaian = models.TextField(help_text="Pencapaian dan hasil yang diperoleh")
    kendala_solusi = models.TextField(help_text="Kendala yang dihadapi dan solusinya")
    saran_perusahaan = models.TextField(help_text="Saran untuk perusahaan")
    saran_kampus = models.TextField(help_text="Saran untuk kampus")
    
    # File laporan
    file_laporan = models.URLField(max_length=500, null=True, blank=True, verbose_name="File Laporan (Firebase URL)")
    
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
    ], default='draft')
    
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Laporan Akhir - {self.konfirmasi.mahasiswa.username}"


class SertifikatCoop(models.Model):
    """Sertifikat yang diberikan kepada mahasiswa yang telah menyelesaikan program coop"""
    konfirmasi = models.OneToOneField(KonfirmasiMagang, on_delete=models.CASCADE, related_name='sertifikat')
    
    # Data sertifikat
    nomor_sertifikat = models.CharField(max_length=50, unique=True)
    nilai_akhir = models.CharField(max_length=2, choices=[
        ('A', 'A (Sangat Baik)'),
        ('B', 'B (Baik)'),
        ('C', 'C (Cukup)'),
        ('D', 'D (Kurang)'),
    ], help_text="Konversi nilai untuk mata kuliah Coop")
    
    # Metadata
    tanggal_kelulusan = models.DateField(auto_now_add=True)
    dikeluarkan_oleh = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'admin'})
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('issued', 'Diterbitkan'),
        ('revoked', 'Dicabut'),
    ], default='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Sertifikat {self.nomor_sertifikat} - {self.konfirmasi.mahasiswa.get_full_name()}"
    
    def generate_nomor_sertifikat(self):
        """Generate unique certificate number"""
        from datetime import datetime
        year = datetime.now().year
        # Count existing certificates this year
        count = SertifikatCoop.objects.filter(
            created_at__year=year
        ).count() + 1
        
        return f"COOP/{year}/{count:04d}/UTS"

    def save(self, *args, **kwargs):
        if not self.nomor_sertifikat:
            self.nomor_sertifikat = self.generate_nomor_sertifikat()
        super().save(*args, **kwargs)


class WeeklyReport(models.Model):
    """Model untuk laporan mingguan mahasiswa yang belum mendapat tempat magang"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_reports')
    week_number = models.PositiveIntegerField()
    week_start_date = models.DateField()
    week_end_date = models.DateField()
    
    # Konten laporan
    main_activities = models.TextField(
        verbose_name="Aktivitas Utama",
        help_text="Aktivitas pencarian magang yang dilakukan minggu ini"
    )
    target_achievement = models.TextField(
        verbose_name="Pencapaian Target",
        help_text="Target yang berhasil dicapai minggu ini"
    )
    companies_applied = models.TextField(
        verbose_name="Perusahaan yang Dilamar",
        help_text="Daftar perusahaan yang sudah dilamar/dihubungi"
    )
    interview_status = models.TextField(
        verbose_name="Status Interview",
        help_text="Update mengenai interview yang sudah/akan dilakukan",
        blank=True
    )
    challenges_faced = models.TextField(
        verbose_name="Kendala yang Dihadapi",
        help_text="Kendala atau tantangan dalam mencari magang",
        blank=True
    )
    help_needed = models.TextField(
        verbose_name="Bantuan yang Diperlukan",
        help_text="Bantuan apa yang dibutuhkan dari admin/mentor",
        blank=True
    )
    next_week_plan = models.TextField(
        verbose_name="Rencana Minggu Depan",
        help_text="Rencana aktivitas untuk minggu depan"
    )
    
    # Progress tracking
    progress_percentage = models.PositiveIntegerField(
        default=0,
        verbose_name="Persentase Progress",
        help_text="Estimasi progress pencarian magang (0-100%)"
    )
    
    # Status
    application_status = models.CharField(
        max_length=50,
        choices=[
            ('searching', 'Masih Mencari'),
            ('applied', 'Sudah Melamar'),
            ('interview_scheduled', 'Interview Dijadwalkan'),
            ('waiting_response', 'Menunggu Respon'),
            ('accepted', 'Diterima'),
            ('rejected', 'Ditolak'),
        ],
        default='searching',
        verbose_name="Status Aplikasi"
    )
    
    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'week_start_date']
        ordering = ['-week_start_date']
    
    def __str__(self):
        return f"Laporan Minggu {self.week_number} - {self.student.get_full_name()}"


class DeadlineReminder(models.Model):
    """Model untuk pengaturan deadline dan reminder sistem"""
    deadline_date = models.DateField(
        verbose_name="Tanggal Deadline",
        help_text="Batas waktu untuk mendapatkan tempat magang"
    )
    reminder_frequency_days = models.PositiveIntegerField(
        default=7,
        verbose_name="Frekuensi Reminder (hari)",
        help_text="Setiap berapa hari reminder dikirim"
    )
    description = models.TextField(
        verbose_name="Deskripsi",
        help_text="Deskripsi atau instruksi mengenai deadline ini"
    )
    email_reminder_enabled = models.BooleanField(
        default=True,
        verbose_name="Email Reminder Aktif",
        help_text="Apakah sistem mengirim email reminder otomatis"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Status Aktif",
        help_text="Apakah pengaturan reminder ini aktif"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Deadline: {self.deadline_date} (Aktif: {'Ya' if self.is_active else 'Tidak'})"
    
    @property
    def days_until_deadline(self):
        """Hitung hari hingga deadline"""
        from django.utils import timezone
        delta = self.deadline_date - timezone.now().date()
        return delta.days
    
    @property
    def is_overdue(self):
        """Cek apakah deadline sudah terlewati"""
        from django.utils import timezone
        return timezone.now().date() > self.deadline_date


class Notification(models.Model):
    """Model untuk notifikasi in-app"""
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('danger', 'Urgent'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="User")
    title = models.CharField(max_length=200, verbose_name="Judul")
    message = models.TextField(verbose_name="Pesan")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info', verbose_name="Tipe")
    is_read = models.BooleanField(default=False, verbose_name="Sudah Dibaca")
    link = models.CharField(max_length=200, blank=True, null=True, verbose_name="Link URL")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Waktu Dibuat")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notifikasi"
        verbose_name_plural = "Notifikasi"

    def __str__(self):
        return f"{self.title} - {self.user.username}"
