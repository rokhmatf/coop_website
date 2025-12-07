from django.urls import path
from . import views

app_name = "coops"

urlpatterns = [
    path("", views.mahasiswa_dashboard, name="mahasiswa_dashboard"),
    path("konfirmasi/", views.konfirmasi_magang, name="konfirmasi_magang"),
    path("status/", views.status_magang, name="status_magang"),
    path("<int:konfirmasi_id>/weekly-report/", views.submit_weekly_report, name="submit_weekly_report"),
    path("lowongan/", views.lowongan, name="lowongan"),
    
    # Laporan Kemajuan (UTS)
    path("laporan-kemajuan/", views.laporan_kemajuan, name="laporan_kemajuan"),
    path("laporan-kemajuan/<str:bulan>/", views.laporan_kemajuan, name="laporan_kemajuan_bulan"),
    path("daftar-laporan-kemajuan/", views.daftar_laporan_kemajuan, name="daftar_laporan_kemajuan"),
    path("laporan-mahasiswa/", views.laporan_mahasiswa, name="laporan_mahasiswa"),
    
    # Laporan Akhir (UAS)
    path("laporan-akhir/", views.laporan_akhir, name="laporan_akhir"),
    
    # Evaluasi Supervisor
    path("evaluasi/<int:konfirmasi_id>/<int:template_id>/", views.evaluasi_supervisor, name="evaluasi_supervisor"),
    path("evaluasi/hasil/<int:konfirmasi_id>/<int:template_id>/", views.hasil_evaluasi, name="hasil_evaluasi"),

    # Admin tracking
    path("tracking-evaluasi/", views.tracking_evaluasi, name="tracking_evaluasi"),
    
    # Sertifikat Coop
    path("sertifikat/", views.sertifikat_coop, name="sertifikat_coop"),
    path("generate-sertifikat/<int:konfirmasi_id>/", views.generate_sertifikat, name="generate_sertifikat"),
    path("download-sertifikat/<int:sertifikat_id>/", views.download_sertifikat, name="download_sertifikat"),
    
    # Weekly Reports
    path("weekly-report/", views.weekly_report, name="weekly_report"),
    path("weekly-reports/", views.weekly_report_list, name="weekly_report_list"),
    path("admin/weekly-reports/", views.admin_weekly_reports, name="admin_weekly_reports"),
    path("admin/deadline-reminder/", views.manage_deadline_reminder, name="manage_deadline_reminder"),

    # Notifications
    path("notifications/get/", views.get_notifications, name="get_notifications"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/mark-all-read/", views.mark_all_notifications_read, name="mark_all_notifications_read"),
]
