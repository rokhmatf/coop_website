from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from coops.models import KonfirmasiMagang, EvaluasiSupervisor, EvaluasiTemplate, LaporanKemajuan
from accounts.models import User

@login_required
def lowongan(request):
    return render(request, "jobs/list_lowongan.html")

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
    
    # Evaluasi yang harus diisi
    evaluasi_list = EvaluasiSupervisor.objects.filter(
        konfirmasi__in=konfirmasi_all,
        status='pending'
    ).select_related('konfirmasi__mahasiswa', 'template')[:5]

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
    
    # Filter template yang belum dikerjakan
    templates = EvaluasiTemplate.objects.filter(
        aktif=True
    ).exclude(id__in=completed_templates)
    
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
        'completed_evaluations': completed_evaluations,
        'selected_template': selected_template,
    }
    
    return render(request, "jobs/evaluasi_form.html", context)

@login_required
def approve_mahasiswa(request, konfirmasi_id):
    """Menerima atau menolak mahasiswa magang"""
    if request.user.role != 'supervisor':
        return JsonResponse({'error': 'Akses ditolak'}, status=403)
    
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
                from coops.models import EvaluasiTemplate
                templates = EvaluasiTemplate.objects.filter(aktif=True)
                for template in templates:
                    EvaluasiSupervisor.objects.get_or_create(
                        konfirmasi=konfirmasi,
                        template=template,
                        defaults={
                            'status': 'pending',
                            'jawaban': {}  # Empty dict as default
                        }
                    )
            
            # TODO: Kirim notifikasi email ke mahasiswa
            # respond with JSON for AJAX, otherwise redirect back with message
            success_message = f"Mahasiswa berhasil {'diterima' if status == 'accepted' else 'ditolak'}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_message})
            else:
                messages.success(request, success_message)
                return redirect('jobs:supervisor_dashboard')
    
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