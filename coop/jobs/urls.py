from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("lowongan/", views.lowongan, name="lowongan"),
    path("profile/", views.profile, name="profile"),

    # Supervisor Dashboard
    path("supervisor/", views.supervisor_dashboard, name="supervisor_dashboard"),
    path("supervisor/evaluasi/<int:konfirmasi_id>/", views.evaluasi_mahasiswa, name="evaluasi_mahasiswa"),
    path("supervisor/approve/<int:konfirmasi_id>/", views.approve_mahasiswa, name="approve_mahasiswa"),
    path("supervisor/laporan/<int:konfirmasi_id>/", views.lihat_laporan, name="lihat_laporan"),
    path("supervisor/selesai/<int:konfirmasi_id>/", views.selesai_konfirmasi, name="selesai_konfirmasi"),

    # Job Posting Management
    path("job/<int:job_id>/", views.job_detail, name="job_detail"),
    path("job/<int:job_id>/apply/", views.apply_to_job, name="apply_to_job"),
    path("my-applications/", views.my_applications, name="my_applications"),
    path("create-job/", views.create_job_posting, name="create_job_posting"),
    path("manage-jobs/", views.manage_job_postings, name="manage_job_postings"),
    path("job/<int:job_id>/edit/", views.edit_job_posting, name="edit_job_posting"),
    path("job/<int:job_id>/delete/", views.delete_job_posting, name="delete_job_posting"),
    path("job/<int:job_id>/applications/", views.review_applications, name="review_applications"),
    path("application/<int:application_id>/update-status/", views.update_application_status, name="update_application_status"),
]
