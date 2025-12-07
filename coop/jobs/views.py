from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from coops.models import KonfirmasiMagang, EvaluasiSupervisor, EvaluasiTemplate, LaporanKemajuan
from accounts.models import User

@login_required
def lowongan(request):
    """Display all active job postings"""
    from .models import JobPosting, JobApplication

    job_postings = JobPosting.objects.filter(
        is_active=True,
        application_deadline__gte=timezone.now().date()
    ).order_by('-posted_date')

    # Check if current user has applied to each job
    if request.user.role == 'mahasiswa':
        applied_jobs = JobApplication.objects.filter(
            mahasiswa=request.user
        ).values_list('job_id', flat=True)
    else:
        applied_jobs = []

    context = {
        'job_postings': job_postings,
        'applied_jobs': applied_jobs,
    }
    return render(request, "jobs/list_lowongan.html", context)

@login_required
def profile(request):
    return redirect("coops:mahasiswa_dashboard")

@login_required
def supervisor_dashboard(request):
    """Dashboard untuk supervisor dengan statistik dan evaluasi"""
    # Pastikan user adalah supervisor atau buat profil supervisor jika belum ada
    if request.user.role != 'supervisor':
        messages.error(request, "Akses ditolak. Anda bukan supervisor.")
        return redirect('login')
    
    supervisor = request.user.supervisor  # This will create supervisor profile if needed
    
    # Ambil semua konfirmasi magang yang diawasi supervisor ini (accepted + pending)
    konfirmasi_all = KonfirmasiMagang.objects.filter(email_supervisor=supervisor.email)
    # accepted subset for some stats
    mahasiswa_magang = konfirmasi_all.filter(status='accepted')
    
    # Auto-create evaluations for accepted students when templates exist
    from coops.models import EvaluasiTemplate
    templates = EvaluasiTemplate.objects.filter(aktif=True)
    
    for konfirmasi in mahasiswa_magang:
        for template in templates:
            # Create evaluation if doesn't exist
            evaluasi, created = EvaluasiSupervisor.objects.get_or_create(
                konfirmasi=konfirmasi,
                template=template,
                defaults={
                    'status': 'pending',
                    'jawaban': {}  # Empty dict as default
                }
            )
    
    # Statistik
    total_mahasiswa = mahasiswa_magang.count()
    
    # Evaluasi yang belum diisi (pending) and completed (use all supervised konfirmasi)
    evaluasi_pending = EvaluasiSupervisor.objects.filter(
        konfirmasi__in=konfirmasi_all,
        status='pending'
    ).count()

    # Evaluasi yang sudah selesai
    evaluasi_completed = EvaluasiSupervisor.objects.filter(
        konfirmasi__in=konfirmasi_all,
        status='completed'
    ).count()
    
    # Laporan bulanan yang tersedia
    laporan_bulanan = LaporanKemajuan.objects.filter(
        konfirmasi__in=konfirmasi_all,
        status='submitted'
    ).count()
    
    # Mahasiswa yang butuh persetujuan
    mahasiswa_pending = konfirmasi_all.filter(status='pending')
    
    # Add evaluation completion status for each mahasiswa
    mahasiswa_magang_with_status = []
    for konfirmasi in mahasiswa_magang:
        # Count total evaluations for this student
        total_evaluations = EvaluasiSupervisor.objects.filter(konfirmasi=konfirmasi).count()
        # Count completed evaluations for this student
        completed_evaluations = EvaluasiSupervisor.objects.filter(
            konfirmasi=konfirmasi, 
            status='completed'
        ).count()
        
        # Check if all evaluations are completed
        all_evaluations_completed = (total_evaluations > 0 and 
                                   completed_evaluations == total_evaluations)
        
        mahasiswa_magang_with_status.append({
            'konfirmasi': konfirmasi,
            'total_evaluations': total_evaluations,
            'completed_evaluations': completed_evaluations,
            'all_evaluations_completed': all_evaluations_completed
        })
    
    # Evaluasi yang harus diisi - only show those within active period
    evaluasi_list = EvaluasiSupervisor.objects.filter(
        konfirmasi__in=konfirmasi_all,
        status='pending'
    ).select_related('konfirmasi__mahasiswa', 'template')

    # Filter evaluasi by period status
    evaluasi_list_filtered = []
    for evaluasi in evaluasi_list:
        evaluasi.period_active = evaluasi.template.can_be_filled()
        evaluasi.period_status = evaluasi.template.period_status_display()
        evaluasi_list_filtered.append(evaluasi)

    evaluasi_list = evaluasi_list_filtered[:5]

    # Overall evaluation counts and breakdown by type (UTS/UAS)
    total_evaluasi = EvaluasiSupervisor.objects.filter(konfirmasi__in=mahasiswa_magang).count()
    uts_total = EvaluasiSupervisor.objects.filter(konfirmasi__in=mahasiswa_magang, template__jenis='uts').count()
    uts_completed = EvaluasiSupervisor.objects.filter(konfirmasi__in=mahasiswa_magang, template__jenis='uts', status='completed').count()
    uas_total = EvaluasiSupervisor.objects.filter(konfirmasi__in=mahasiswa_magang, template__jenis='uas').count()
    uas_completed = EvaluasiSupervisor.objects.filter(konfirmasi__in=mahasiswa_magang, template__jenis='uas', status='completed').count()

    # percentages (integers)
    uts_percent = int((uts_completed / uts_total) * 100) if uts_total else 0
    uas_percent = int((uas_completed / uas_total) * 100) if uas_total else 0
    
    # Check if there are any students with pending evaluations
    has_pending_evaluations = any(not item['all_evaluations_completed'] for item in mahasiswa_magang_with_status)
    
    context = {
        'total_mahasiswa': total_mahasiswa,
        'evaluasi_pending': evaluasi_pending,
        'evaluasi_completed': evaluasi_completed,
        'laporan_bulanan': laporan_bulanan,
        'mahasiswa_magang': mahasiswa_magang,
        'mahasiswa_magang_with_status': mahasiswa_magang_with_status,
        'mahasiswa_pending': mahasiswa_pending,
        'evaluasi_list': evaluasi_list,
        'total_evaluasi': total_evaluasi,
        'uts_total': uts_total,
        'uts_completed': uts_completed,
        'uts_percent': uts_percent,
        'uas_total': uas_total,
        'uas_completed': uas_completed,
        'uas_percent': uas_percent,
        'konfirmasi_all': konfirmasi_all,
        'evaluasi_templates': templates,
        'has_pending_evaluations': has_pending_evaluations,
    }
    
    return render(request, "jobs/supervisor_dashboard.html", context)

@login_required
def evaluasi_mahasiswa(request, konfirmasi_id):
    """Form untuk mengisi evaluasi mahasiswa"""
    if request.user.role != 'supervisor':
        messages.error(request, "Akses ditolak.")
        return redirect('login')
    
    konfirmasi = get_object_or_404(KonfirmasiMagang, id=konfirmasi_id)
    supervisor = request.user.supervisor
    
    # Pastikan supervisor yang tepat
    if konfirmasi.email_supervisor != supervisor.email:
        messages.error(request, "Anda tidak memiliki akses untuk mahasiswa ini.")
        return redirect('jobs:supervisor_dashboard')
    
    # Ambil template evaluasi aktif yang belum diselesaikan untuk mahasiswa ini
    completed_templates = EvaluasiSupervisor.objects.filter(
        konfirmasi=konfirmasi,
        status='completed'
    ).values_list('template_id', flat=True)

    # Filter template yang belum dikerjakan dan check periode
    all_templates = EvaluasiTemplate.objects.filter(
        aktif=True
    ).exclude(id__in=completed_templates)

    # Separate templates into available and unavailable based on period
    available_templates = []
    unavailable_templates = []
    for template in all_templates:
        if template.can_be_filled():
            available_templates.append(template)
        else:
            unavailable_templates.append(template)

    templates = available_templates
    
    # Pre-select template if provided in GET parameter (for quick-evaluate flow)
    selected_template_id = request.GET.get('template')
    selected_template = None
    if selected_template_id:
        try:
            selected_template = templates.get(id=selected_template_id)
        except EvaluasiTemplate.DoesNotExist:
            pass
    
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        template = get_object_or_404(EvaluasiTemplate, id=template_id)

        # Validate that template can be filled (period check)
        if not template.can_be_filled():
            messages.error(request, f"Evaluasi {template.nama} tidak dapat diisi saat ini. {template.period_status_display()}.")
            return redirect('jobs:evaluasi_mahasiswa', konfirmasi_id=konfirmasi_id)

        # Kumpulkan jawaban dari form
        jawaban = {}
        for key, value in request.POST.items():
            if key.startswith('jawaban_'):
                question_index = key.replace('jawaban_', '')
                jawaban[question_index] = value

        # Simpan atau update evaluasi
        evaluasi, created = EvaluasiSupervisor.objects.get_or_create(
            konfirmasi=konfirmasi,
            template=template,
            defaults={
                'jawaban': jawaban,
                'status': 'completed',
                'submitted_at': timezone.now()
            }
        )

        if not created:
            evaluasi.jawaban = jawaban
            evaluasi.status = 'completed'
            evaluasi.submitted_at = timezone.now()
            evaluasi.save()

        messages.success(request, f"Evaluasi {template.nama} berhasil disimpan!")
        return redirect('jobs:supervisor_dashboard')
    
    # Ambil evaluasi yang sudah selesai untuk informasi tambahan
    completed_evaluations = EvaluasiSupervisor.objects.filter(
        konfirmasi=konfirmasi,
        status='completed'
    ).select_related('template')
    
    context = {
        'konfirmasi': konfirmasi,
        'templates': templates,
        'unavailable_templates': unavailable_templates,
        'completed_evaluations': completed_evaluations,
        'selected_template': selected_template,
    }

    return render(request, "jobs/evaluasi_form.html", context)

@login_required
def approve_mahasiswa(request, konfirmasi_id):
    """Menerima atau menolak mahasiswa magang"""
    if request.user.role != 'supervisor':
        return JsonResponse({'error': 'Akses ditolak'}, status=403)
<<<<<<< HEAD

    konfirmasi = get_object_or_404(KonfirmasiMagang, id=konfirmasi_id)
    supervisor = request.user.supervisor

    if konfirmasi.email_supervisor != supervisor.email:
        return JsonResponse({'error': 'Tidak memiliki akses'}, status=403)

    if request.method == 'POST':
        status = request.POST.get('status')
        catatan = request.POST.get('catatan', '')
        rejection_reason = request.POST.get('rejection_reason', '')

        if status in ['accepted', 'rejected']:
            konfirmasi.status = status
            konfirmasi.approved_by = request.user

            if status == 'accepted':
                konfirmasi.approved_at = timezone.now()
                konfirmasi.approval_notes = catatan
                konfirmasi.rejected_at = None
                konfirmasi.rejection_reason = None

                # Auto-create evaluations when student is accepted
=======
    
    konfirmasi = get_object_or_404(KonfirmasiMagang, id=konfirmasi_id)
    supervisor = request.user.supervisor
    
    if konfirmasi.email_supervisor != supervisor.email:
        return JsonResponse({'error': 'Tidak memiliki akses'}, status=403)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        catatan = request.POST.get('catatan', '')
        
        if status in ['accepted', 'rejected']:
            konfirmasi.status = status
            konfirmasi.save()
            
            # Auto-create evaluations when student is accepted
            if status == 'accepted':
>>>>>>> 85e3e31ec65f7120152caae6ad2dd1b07684e8a1
                from coops.models import EvaluasiTemplate
                templates = EvaluasiTemplate.objects.filter(aktif=True)
                for template in templates:
                    EvaluasiSupervisor.objects.get_or_create(
                        konfirmasi=konfirmasi,
                        template=template,
                        defaults={
                            'status': 'pending',
<<<<<<< HEAD
                            'jawaban': {}
                        }
                    )

                # Send notification to mahasiswa
                from coops.models import Notification
                Notification.objects.create(
                    user=konfirmasi.mahasiswa,
                    title="Magang Disetujui!",
                    message=f"Selamat! Magang Anda di {konfirmasi.nama_perusahaan} telah disetujui oleh supervisor. {catatan}",
                    notification_type='success',
                    link='/coops/mahasiswa_dashboard/'
                )

            else:
                konfirmasi.rejected_at = timezone.now()
                konfirmasi.rejection_reason = rejection_reason
                konfirmasi.approval_notes = catatan
                konfirmasi.approved_at = None

                # Send notification to mahasiswa
                from coops.models import Notification
                Notification.objects.create(
                    user=konfirmasi.mahasiswa,
                    title="Magang Ditolak",
                    message=f"Maaf, magang Anda di {konfirmasi.nama_perusahaan} ditolak. Alasan: {rejection_reason}. Silakan coba lagi atau hubungi supervisor untuk informasi lebih lanjut.",
                    notification_type='danger',
                    link='/coops/mahasiswa_dashboard/'
                )

            konfirmasi.save()

            # Send notification to kaprodi if mahasiswa has jurusan
            try:
                mahasiswa_obj = konfirmasi.mahasiswa.mahasiswa
                if mahasiswa_obj.jurusan:
                    from accounts.models import Kaprodi
                    kaprodis = Kaprodi.objects.filter(jurusan=mahasiswa_obj.jurusan)
                    for kaprodi in kaprodis:
                        from coops.models import Notification
                        Notification.objects.create(
                            user=kaprodi.user,
                            title=f"Update Status Magang - {mahasiswa_obj.nama}",
                            message=f"Mahasiswa {mahasiswa_obj.nama} ({mahasiswa_obj.nim}) telah {'diterima' if status == 'accepted' else 'ditolak'} magang di {konfirmasi.nama_perusahaan}.",
                            notification_type='info',
                            link='/accounts/kaprodi-dashboard/'
                        )
            except Exception:
                pass

=======
                            'jawaban': {}  # Empty dict as default
                        }
                    )
            
            # TODO: Kirim notifikasi email ke mahasiswa
            # respond with JSON for AJAX, otherwise redirect back with message
>>>>>>> 85e3e31ec65f7120152caae6ad2dd1b07684e8a1
            success_message = f"Mahasiswa berhasil {'diterima' if status == 'accepted' else 'ditolak'}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_message})
            else:
                messages.success(request, success_message)
                return redirect('jobs:supervisor_dashboard')
<<<<<<< HEAD

=======
    
>>>>>>> 85e3e31ec65f7120152caae6ad2dd1b07684e8a1
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def lihat_laporan(request, konfirmasi_id):
    """Melihat laporan kemajuan mahasiswa"""
    if request.user.role != 'supervisor':
        messages.error(request, "Akses ditolak.")
        return redirect('login')
    
    konfirmasi = get_object_or_404(KonfirmasiMagang, id=konfirmasi_id)
    supervisor = request.user.supervisor
    
    if konfirmasi.email_supervisor != supervisor.email:
        messages.error(request, "Anda tidak memiliki akses untuk mahasiswa ini.")
        return redirect('jobs:supervisor_dashboard')
    
    # Ambil semua laporan kemajuan
    laporan_list = LaporanKemajuan.objects.filter(
        konfirmasi=konfirmasi
    ).order_by('-bulan')
    
    context = {
        'konfirmasi': konfirmasi,
        'laporan_list': laporan_list,
    }
    
    return render(request, "jobs/laporan_detail.html", context)

@login_required
def selesai_konfirmasi(request, konfirmasi_id):
    """Tandai konfirmasi magang sebagai selesai atau selesaikan proses bimbingan.
    """
    if request.method != 'POST':
        messages.error(request, "Metode tidak diperbolehkan.")
        return redirect('jobs:supervisor_dashboard')

    konfirmasi = get_object_or_404(KonfirmasiMagang, id=konfirmasi_id)
    # ensure the user is supervisor for this konfirmasi
    supervisor = getattr(request.user, 'supervisor', None)
    if not supervisor or konfirmasi.email_supervisor != supervisor.email:
        messages.error(request, "Anda tidak memiliki akses untuk mahasiswa ini.")
        return redirect('jobs:supervisor_dashboard')

    # Mark as completed (use existing status choice defined in model)
    konfirmasi.status = 'completed'
    konfirmasi.save()

    # Update all evaluations for this konfirmasi to 'finished'
    EvaluasiSupervisor.objects.filter(konfirmasi=konfirmasi).update(status='finished')

    messages.success(request, "Konfirmasi magang berhasil diselesaikan.")
    return redirect('jobs:supervisor_dashboard')

@login_required
def job_detail(request, job_id):
    """View job posting details"""
    from .models import JobPosting, JobApplication

    job = get_object_or_404(JobPosting, id=job_id)
    has_applied = False
    application = None

    if request.user.role == 'mahasiswa':
        try:
            application = JobApplication.objects.get(job=job, mahasiswa=request.user)
            has_applied = True
        except JobApplication.DoesNotExist:
            pass

    context = {
        'job': job,
        'has_applied': has_applied,
        'application': application,
    }
    return render(request, "jobs/job_detail.html", context)

@login_required
def apply_to_job(request, job_id):
    """Apply to a job posting"""
    from .models import JobPosting, JobApplication
    from accounts.models import Mahasiswa

    if request.user.role != 'mahasiswa':
        messages.error(request, "Hanya mahasiswa yang dapat melamar pekerjaan.")
        return redirect('jobs:lowongan')

    job = get_object_or_404(JobPosting, id=job_id, is_active=True)

    # Check if already applied
    if JobApplication.objects.filter(job=job, mahasiswa=request.user).exists():
        messages.warning(request, "Anda sudah melamar pekerjaan ini.")
        return redirect('jobs:job_detail', job_id=job_id)

    # Check if job deadline has passed
    if job.is_expired:
        messages.error(request, "Lowongan ini sudah ditutup.")
        return redirect('jobs:job_detail', job_id=job_id)

    if request.method == 'POST':
        cv_url = request.POST.get('cv_url')
        cover_letter = request.POST.get('cover_letter', '')

        if not cv_url:
            messages.error(request, "CV URL wajib diisi.")
            return redirect('jobs:apply_to_job', job_id=job_id)

        # Create application
        application = JobApplication.objects.create(
            job=job,
            mahasiswa=request.user,
            cv_url=cv_url,
            cover_letter=cover_letter,
            status='applied'
        )

        messages.success(request, f"Berhasil melamar ke {job.title}!")
        return redirect('jobs:my_applications')

    # Get mahasiswa CV from profile if available
    try:
        mahasiswa = Mahasiswa.objects.get(email=request.user)
        default_cv = mahasiswa.cv
    except Mahasiswa.DoesNotExist:
        default_cv = ''

    context = {
        'job': job,
        'default_cv': default_cv,
    }
    return render(request, "jobs/apply_job.html", context)

@login_required
def my_applications(request):
    """View all job applications by current user"""
    from .models import JobApplication

    if request.user.role != 'mahasiswa':
        messages.error(request, "Akses ditolak.")
        return redirect('jobs:lowongan')

    applications = JobApplication.objects.filter(
        mahasiswa=request.user
    ).select_related('job').order_by('-applied_date')

    context = {
        'applications': applications,
    }
    return render(request, "jobs/my_applications.html", context)

@login_required
def create_job_posting(request):
    """Create a new job posting (Admin only)"""
    from .models import JobPosting

    if request.user.role not in ['admin', 'supervisor']:
        messages.error(request, "Akses ditolak. Hanya admin dan supervisor yang dapat membuat lowongan.")
        return redirect('jobs:lowongan')

    if request.method == 'POST':
        title = request.POST.get('title')
        company_name = request.POST.get('company_name')
        company_logo = request.POST.get('company_logo', '')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')
        location = request.POST.get('location')
        job_type = request.POST.get('job_type')
        salary_range = request.POST.get('salary_range', '')
        application_deadline = request.POST.get('application_deadline')

        if not all([title, company_name, description, requirements, location, job_type, application_deadline]):
            messages.error(request, "Semua field wajib diisi kecuali logo dan gaji.")
            return render(request, "jobs/create_job_posting.html", {'job_types': JobPosting.JOB_TYPE_CHOICES})

        job = JobPosting.objects.create(
            title=title,
            company_name=company_name,
            company_logo=company_logo,
            description=description,
            requirements=requirements,
            location=location,
            job_type=job_type,
            salary_range=salary_range,
            application_deadline=application_deadline,
            created_by=request.user,
            is_active=True
        )

        messages.success(request, f"Lowongan '{job.title}' berhasil dibuat!")
        return redirect('jobs:manage_job_postings')

    context = {
        'job_types': JobPosting.JOB_TYPE_CHOICES,
    }
    return render(request, "jobs/create_job_posting.html", context)

@login_required
def manage_job_postings(request):
    """Manage all job postings (Admin/Supervisor)"""
    from .models import JobPosting

    if request.user.role not in ['admin', 'supervisor']:
        messages.error(request, "Akses ditolak.")
        return redirect('jobs:lowongan')

    job_postings = JobPosting.objects.all().order_by('-posted_date')

    context = {
        'job_postings': job_postings,
    }
    return render(request, "jobs/manage_job_postings.html", context)

@login_required
def edit_job_posting(request, job_id):
    """Edit a job posting"""
    from .models import JobPosting

    if request.user.role not in ['admin', 'supervisor']:
        messages.error(request, "Akses ditolak.")
        return redirect('jobs:lowongan')

    job = get_object_or_404(JobPosting, id=job_id)

    if request.method == 'POST':
        job.title = request.POST.get('title')
        job.company_name = request.POST.get('company_name')
        job.company_logo = request.POST.get('company_logo', '')
        job.description = request.POST.get('description')
        job.requirements = request.POST.get('requirements')
        job.location = request.POST.get('location')
        job.job_type = request.POST.get('job_type')
        job.salary_range = request.POST.get('salary_range', '')
        job.application_deadline = request.POST.get('application_deadline')
        job.is_active = request.POST.get('is_active') == 'on'

        job.save()

        messages.success(request, f"Lowongan '{job.title}' berhasil diupdate!")
        return redirect('jobs:manage_job_postings')

    context = {
        'job': job,
        'job_types': JobPosting.JOB_TYPE_CHOICES,
    }
    return render(request, "jobs/edit_job_posting.html", context)

@login_required
def delete_job_posting(request, job_id):
    """Delete a job posting"""
    from .models import JobPosting

    if request.user.role not in ['admin', 'supervisor']:
        return JsonResponse({'error': 'Akses ditolak'}, status=403)

    job = get_object_or_404(JobPosting, id=job_id)

    if request.method == 'POST':
        job_title = job.title
        job.delete()
        messages.success(request, f"Lowongan '{job_title}' berhasil dihapus!")
        return redirect('jobs:manage_job_postings')

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def review_applications(request, job_id):
    """Review applications for a job posting"""
    from .models import JobPosting, JobApplication

    if request.user.role not in ['admin', 'supervisor']:
        messages.error(request, "Akses ditolak.")
        return redirect('jobs:lowongan')

    job = get_object_or_404(JobPosting, id=job_id)
    applications = JobApplication.objects.filter(job=job).select_related('mahasiswa').order_by('-applied_date')

    context = {
        'job': job,
        'applications': applications,
    }
    return render(request, "jobs/review_applications.html", context)

@login_required
def update_application_status(request, application_id):
    """Update status of a job application"""
    from .models import JobApplication

    if request.user.role not in ['admin', 'supervisor']:
        return JsonResponse({'error': 'Akses ditolak'}, status=403)

    application = get_object_or_404(JobApplication, id=application_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')

        if status in dict(JobApplication.STATUS_CHOICES):
            application.status = status
            application.notes = notes
            application.save()

            messages.success(request, f"Status aplikasi berhasil diupdate menjadi '{application.get_status_display()}'!")

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Status berhasil diupdate'})
            else:
                return redirect('jobs:review_applications', job_id=application.job.id)

    return JsonResponse({'error': 'Invalid request'}, status=400)