from django import forms
from .models import KonfirmasiMagang, WeeklyReport, DeadlineReminder

class KonfirmasiMagangForm(forms.ModelForm):
    class Meta:
        model = KonfirmasiMagang
        exclude = ["mahasiswa", "status"]
        widgets = {
            "periode": forms.TextInput(attrs={"class": "form-control", "placeholder": "Contoh: 2025/1"}),
            "posisi": forms.TextInput(attrs={"class": "form-control"}),
            "nama_perusahaan": forms.TextInput(attrs={"class": "form-control"}),
            "alamat_perusahaan": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "bidang_usaha": forms.TextInput(attrs={"class": "form-control"}),
            "nama_supervisor": forms.TextInput(attrs={"class": "form-control"}),
            "email_supervisor": forms.EmailInput(attrs={"class": "form-control"}),
            "wa_supervisor": forms.TextInput(attrs={"class": "form-control"}),
            # asumsikan field file bernama 'surat_penerimaan'
            "surat_penerimaan": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
        }

class WeeklyReportForm(forms.ModelForm):
    class Meta:
        model = WeeklyReport
        fields = [
            'week_number', 'week_start_date', 'week_end_date',
            'main_activities', 'target_achievement', 'companies_applied',
            'interview_status', 'challenges_faced', 'help_needed',
            'next_week_plan', 'progress_percentage', 'application_status'
        ]
        widgets = {
            'week_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Contoh: 1'
            }),
            'week_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'week_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'main_activities': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Jelaskan aktivitas utama pencarian magang yang dilakukan minggu ini...'
            }),
            'target_achievement': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Target apa saja yang berhasil dicapai minggu ini...'
            }),
            'companies_applied': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Sebutkan perusahaan yang sudah dilamar atau dihubungi...'
            }),
            'interview_status': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': 'Update mengenai interview (jika ada)...'
            }),
            'challenges_faced': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Kendala atau tantangan yang dihadapi (jika ada)...'
            }),
            'help_needed': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': 'Bantuan apa yang dibutuhkan dari admin/mentor (jika ada)...'
            }),
            'next_week_plan': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Rencana aktivitas untuk minggu depan...'
            }),
            'progress_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'placeholder': 'Contoh: 70'
            }),
            'application_status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'week_number': 'Minggu ke-',
            'week_start_date': 'Tanggal Mulai Minggu',
            'week_end_date': 'Tanggal Akhir Minggu',
            'main_activities': 'Aktivitas Utama',
            'target_achievement': 'Pencapaian Target',
            'companies_applied': 'Perusahaan yang Dilamar',
            'interview_status': 'Status Interview',
            'challenges_faced': 'Kendala yang Dihadapi',
            'help_needed': 'Bantuan yang Diperlukan',
            'next_week_plan': 'Rencana Minggu Depan',
            'progress_percentage': 'Persentase Progress (%)',
            'application_status': 'Status Aplikasi',
        }

class DeadlineReminderForm(forms.ModelForm):
    class Meta:
        model = DeadlineReminder
        fields = ['deadline_date', 'reminder_frequency_days', 'description', 'email_reminder_enabled']
        widgets = {
            'deadline_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'reminder_frequency_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '7'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Deskripsi atau instruksi mengenai deadline...'
            }),
            'email_reminder_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'deadline_date': 'Tanggal Deadline',
            'reminder_frequency_days': 'Frekuensi Reminder (hari)',
            'description': 'Deskripsi',
            'email_reminder_enabled': 'Aktifkan Email Reminder',
        }
