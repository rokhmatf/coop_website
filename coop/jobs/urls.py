from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("lowongan/", views.lowongan, name="lowongan"),
    path("profile/", views.profile, name="profile"),
    path("supervisor/", views.supervisor_dashboard, name="supervisor_dashboard"),
    path("supervisor/evaluasi/<int:konfirmasi_id>/", views.evaluasi_mahasiswa, name="evaluasi_mahasiswa"),
    path("supervisor/approve/<int:konfirmasi_id>/", views.approve_mahasiswa, name="approve_mahasiswa"),
    path("supervisor/laporan/<int:konfirmasi_id>/", views.lihat_laporan, name="lihat_laporan"),
    path("supervisor/selesai/<int:konfirmasi_id>/", views.selesai_konfirmasi, name="selesai_konfirmasi"),
]
