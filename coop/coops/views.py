from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.decorators import mahasiswa_required
from django.contrib import messages
from .models import KonfirmasiMagang, LaporanKemajuan
from accounts.models import Mahasiswa
from django.http import HttpResponse
from django.template import loader
from .forms import WeeklyReportForm
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import date, timedelta


# Mahasiswa isi konfirmasi magang
@login_required
def konfirmasi_magang(request):
    if request.user.role != "mahasiswa":
        return redirect("/")  # hanya mahasiswa

    if request.method == "POST":
        # ambil field dari form HTML
        periode_awal = request.POST.get('periode_awal', '').strip()
        periode_akhir = request.POST.get('periode_akhir', '').strip()
        posisi = request.POST.get('posisi', '').strip()
        nama_perusahaan = request.POST.get('nama_perusahaan', '').strip()
        alamat_perusahaan = request.POST.get('alamat_perusahaan', '').strip()
        bidang_usaha = request.POST.get('bidang_usaha', '').strip()
        nama_supervisor = request.POST.get('nama_supervisor', '').strip()
        email_supervisor = request.POST.get('email_supervisor', '').strip()
        wa_supervisor = request.POST.get('wa_supervisor', '').strip()

        # file
        surat = request.FILES.get('surat_penerimaan')  # name input file

        # validasi sederhana
        errors = []
        if not periode_awal or not periode_akhir:
            errors.append("Periode harus diisi.")
        if not posisi:
            errors.append("Posisi harus diisi.")
        if not nama_perusahaan:
            errors.append("Nama perusahaan harus diisi.")
        # ... tambah validasi lain sesuai kebutuhan

        # contoh validasi file (opsional)
        if surat:
            # batasi tipe dan ukuran (contoh)
            if surat.size > 5 * 1024 * 1024:  # 5 MB
                errors.append("File terlalu besar (maks 5MB).")
            if not surat.content_type in ("application/pdf", "image/jpeg", "image/png"):
                errors.append("Format file harus PDF/JPEG/PNG.")

        if errors:
            for e in errors:
                messages.error(request, e)
            # kembalikan ke form, Anda mungkin ingin menyimpan field agar tetap tampil
            return render(request, "coops/konfirmasi_magang.html", {"form_values": request.POST})

        # simpan ke model
        # Jika sudah ada KonfirmasiMagang untuk user ini, update record
        km = KonfirmasiMagang.objects.filter(mahasiswa=request.user).first()
        if km:
            # update existing
            km.periode_awal = periode_awal
            km.periode_akhir = periode_akhir
            km.posisi = posisi
            km.nama_perusahaan = nama_perusahaan
            km.alamat_perusahaan = alamat_perusahaan
            km.bidang_usaha = bidang_usaha
            km.nama_supervisor = nama_supervisor
            km.email_supervisor = email_supervisor
            km.wa_supervisor = wa_supervisor
            if surat:
                km.surat_penerimaan = surat
            # keep current status (or reset to pending) — choose pending for re-submission
            km.status = 'pending'
            km.save()
            messages.success(request, "Konfirmasi magang berhasil diperbarui.")
        else:
            # create new
            km = KonfirmasiMagang()
            km.mahasiswa = request.user  # pastikan request.user adalah Mahasiswa terkait
            km.periode_awal = periode_awal
            km.periode_akhir = periode_akhir
            km.posisi = posisi
            km.nama_perusahaan = nama_perusahaan
            km.alamat_perusahaan = alamat_perusahaan
            km.bidang_usaha = bidang_usaha
            km.nama_supervisor = nama_supervisor
            km.email_supervisor = email_supervisor
            km.wa_supervisor = wa_supervisor
            if surat:
                km.surat_penerimaan = surat  # field FileField di model
            km.status = 'pending'  # contoh default status
            km.save()
            messages.success(request, "Konfirmasi magang berhasil dikirim.")

        # set Mahasiswa.magang flag if Mahasiswa record exists
        try:
            m = request.user.mahasiswa
            m.magang = True
            m.save()
        except Exception:
            pass

        # redirect to mahasiswa dashboard
        return redirect('coops:mahasiswa_dashboard')
    # method GET
    return render(request, "coops/konfirmasi_magang.html")

# Admin lihat status magang semua mahasiswa
@login_required
def status_magang(request):
    if request.user.role != "admin":
        return redirect("/")  # hanya admin

    # Tampilkan semua mahasiswa beserta konfirmasi magang jika ada
    from accounts.models import Mahasiswa

    mahasiswa_qs = Mahasiswa.objects.select_related('email').all()
    # Bangun list of tuples: (mahasiswa, magang_or_none)
    mahasiswa_list = []
    for m in mahasiswa_qs:
        magang = KonfirmasiMagang.objects.filter(mahasiswa=m.email).first()
        mahasiswa_list.append((m, magang))

    # Calculate statistics
    all_konfirmasi = KonfirmasiMagang.objects.all()
    accepted_count = all_konfirmasi.filter(status__in=['accepted', 'completed']).count()
    pending_count = all_konfirmasi.filter(status='pending').count()
    rejected_count = all_konfirmasi.filter(status='rejected').count()

    context = {
        'mahasiswa_list': mahasiswa_list,
        'accepted_count': accepted_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
    }

    template = loader.get_template("coops/status_magang.html")
    return HttpResponse(template.render(context, request))


@login_required
def submit_weekly_report(request, konfirmasi_id):
    try:
        konfirmasi = KonfirmasiMagang.objects.get(id=konfirmasi_id)
    except KonfirmasiMagang.DoesNotExist:
        return redirect('coops:mahasiswa_dashboard')

    if request.method == 'POST':
        form = WeeklyReportForm(request.POST)
        if form.is_valid():
            wr = form.save(commit=False)
            wr.konfirmasi = konfirmasi
            wr.save()
            messages.success(request, 'Laporan mingguan berhasil disimpan.')
            return redirect('coops:mahasiswa_dashboard')
    else:
        form = WeeklyReportForm()

    return render(request, 'coops/submit_weekly_report.html', {'form': form, 'konfirmasi': konfirmasi})

@mahasiswa_required
def mahasiswa_dashboard(request):
    # Safely obtain related Mahasiswa and KonfirmasiMagang objects and pass
    # them into the template to avoid template attribute-lookup errors.
    mahasiswa_obj = None
    magang_obj = None

    try:
        mahasiswa_obj = request.user.mahasiswa
    except Exception:
        mahasiswa_obj = None

    if mahasiswa_obj:
        # KonfirmasiMagang.mahasiswa is a OneToOneField to User, so query by
        # request.user (not Mahasiswa). Use .filter().first() to avoid
        # DoesNotExist exceptions.
        magang_obj = KonfirmasiMagang.objects.filter(mahasiswa=request.user).first()

    return render(request, "coops/mahasiswa_dashboard.html", {"mahasiswa": mahasiswa_obj, "magang": magang_obj})


@login_required
def lowongan(request):
    # Render the jobs listing directly so the `lowongan` route under
    # the `coops` app serves the page without redirecting to the jobs app.
    # This keeps the URL `/coops/lowongan/` functional even if the jobs
    # app changes, and avoids an unnecessary HTTP redirect.
    return render(request, "jobs/list_lowongan.html")


@login_required
def tracking_evaluasi(request):
    """View untuk admin melihat tracking evaluasi supervisor"""
    if request.user.role != "admin":
        messages.error(request, "Akses ditolak. Anda bukan admin.")
        return redirect("/")

    from .models import EvaluasiTemplate, EvaluasiSupervisor
    
    tracking_data = []
    
    # Loop through each evaluation template
    for template in EvaluasiTemplate.objects.filter(aktif=True):
        # Get all internships with status accepted or completed
        # Note: "status='accepted' or 'completed'" would evaluate to 'accepted' in Python,
        # so use __in to match multiple values.
        accepted_konfirmasi = KonfirmasiMagang.objects.filter(status__in=['accepted', 'completed'])

        # Get evaluation data for this template
        evaluations = EvaluasiSupervisor.objects.filter(template=template)

        # Calculate statistics
        total_supervisors = accepted_konfirmasi.count()
        completed = evaluations.filter(status__in=['completed', 'finished']).count()
        pending = total_supervisors - completed
        completion_rate = int((completed / total_supervisors) * 100) if total_supervisors > 0 else 0

        # Get detailed supervisor info
        supervisor_details = []
        for konfirmasi in accepted_konfirmasi:
            try:
                evaluation = evaluations.get(konfirmasi=konfirmasi)
                status = evaluation.status
                submitted_date = evaluation.submitted_at
            except EvaluasiSupervisor.DoesNotExist:
                status = 'not_created'
                submitted_date = None

            supervisor_details.append({
                'konfirmasi': konfirmasi,
                'status': status,
                'submitted_date': submitted_date
            })

        tracking_data.append({
            'template': template,
            'total_supervisors': total_supervisors,
            'completed': completed,
            'pending': pending,
            'completion_rate': completion_rate,
            'supervisor_details': supervisor_details
        })
    
    context = {
        'tracking_data': tracking_data
    }
    
    return render(request, 'coops/tracking_evaluasi.html', context)


@login_required
@mahasiswa_required
def laporan_kemajuan(request, bulan=None):
    """View untuk mahasiswa mengisi laporan kemajuan (UTS)"""
    # Cari konfirmasi magang mahasiswa
    try:
        konfirmasi = KonfirmasiMagang.objects.get(mahasiswa=request.user, status='accepted')
    except KonfirmasiMagang.DoesNotExist:
        messages.error(request, 'Anda belum memiliki konfirmasi magang yang diterima.')
        return redirect('coops:mahasiswa_dashboard')
    
    if request.method == 'POST':
        # Ambil data dari form
        from .models import LaporanKemajuan
        from datetime import datetime
        
        # Parse bulan dari form atau gunakan bulan sekarang
        bulan_input = request.POST.get('bulan')
        if bulan_input:
            try:
                # Convert dari format "2025-10" ke date object (hari pertama bulan)
                bulan_laporan = datetime.strptime(bulan_input + '-01', '%Y-%m-%d').date()
            except ValueError:
                bulan_laporan = timezone.now().date().replace(day=1)
        else:
            bulan_laporan = timezone.now().date().replace(day=1)
        
        # Determine action (draft or submit)
        action = request.POST.get('action', 'submit')
        status = 'draft' if action == 'draft' else 'submitted'
        
        # Cek apakah laporan sudah ada untuk mahasiswa dan bulan ini
        existing_laporan = LaporanKemajuan.objects.filter(
            konfirmasi=konfirmasi, 
            bulan=bulan_laporan
        ).first()
        
        try:
            if existing_laporan:
                # Update existing
                existing_laporan.profil_perusahaan = request.POST.get('profil_perusahaan')
                existing_laporan.jobdesk = request.POST.get('jobdesk')
                existing_laporan.suasana_lingkungan = request.POST.get('suasana_lingkungan')
                existing_laporan.manfaat_perkuliahan = request.POST.get('manfaat_perkuliahan')
                existing_laporan.kebutuhan_pembelajaran = request.POST.get('kebutuhan_pembelajaran')
                existing_laporan.status = status
                if status == 'submitted':
                    existing_laporan.submitted_at = timezone.now()
                existing_laporan.save()
                message = 'Laporan kemajuan berhasil diperbarui.'
                if status == 'submitted':
                    message = 'Laporan kemajuan berhasil dikirim.'
                messages.success(request, message)
            else:
                # Create new
                laporan = LaporanKemajuan.objects.create(
                    konfirmasi=konfirmasi,
                    bulan=bulan_laporan,
                    profil_perusahaan=request.POST.get('profil_perusahaan'),
                    jobdesk=request.POST.get('jobdesk'),
                    suasana_lingkungan=request.POST.get('suasana_lingkungan'),
                    manfaat_perkuliahan=request.POST.get('manfaat_perkuliahan'),
                    kebutuhan_pembelajaran=request.POST.get('kebutuhan_pembelajaran'),
                    status=status,
                    submitted_at=timezone.now() if status == 'submitted' else None
                )
                message = 'Laporan kemajuan berhasil disimpan.'
                if status == 'submitted':
                    message = 'Laporan kemajuan berhasil dikirim.'
                messages.success(request, message)
                
            return redirect('coops:mahasiswa_dashboard')
            
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    # GET request - tampilkan form
    from .models import LaporanKemajuan
    from datetime import datetime
    
    # Set default bulan ke bulan sekarang (hari pertama)
    if not bulan:
        bulan_date = timezone.now().date().replace(day=1)
    else:
        try:
            # Parse bulan dari URL parameter jika ada
            bulan_date = datetime.strptime(bulan + '-01', '%Y-%m-%d').date()
        except ValueError:
            bulan_date = timezone.now().date().replace(day=1)
    
    existing_laporan = LaporanKemajuan.objects.filter(
        konfirmasi=konfirmasi,
        bulan=bulan_date
    ).first()
    
    # Generate available months (last 6 months)
    today = timezone.now().date()
    available_months = []
    for i in range(6):
        if i == 0:
            month = today.replace(day=1)
        else:
            # Go back i months
            year = today.year
            month_num = today.month - i
            if month_num <= 0:
                month_num += 12
                year -= 1
            month = date(year, month_num, 1)
        available_months.append(month)
    
    context = {
        'laporan': existing_laporan,
        'bulan': bulan_date,
        'bulan_str': bulan_date.strftime('%Y-%m'),  # For HTML input format
        'bulan_display': bulan_date.strftime('%B %Y'),  # For display
        'konfirmasi': konfirmasi,
        'is_submitted': existing_laporan.status == 'submitted' if existing_laporan else False,
        'available_months': available_months
    }
    
    return render(request, 'coops/laporan_kemajuan_form.html', context)


@login_required  
@mahasiswa_required
def laporan_akhir(request):
    """View untuk mahasiswa mengisi laporan akhir (UAS)"""
    # Cari konfirmasi magang mahasiswa
    try:
        konfirmasi = KonfirmasiMagang.objects.get(mahasiswa=request.user, status='accepted')
    except KonfirmasiMagang.DoesNotExist:
        messages.error(request, 'Anda belum memiliki konfirmasi magang yang diterima.')
        return redirect('coops:mahasiswa_dashboard')
        
    if request.method == 'POST':
        from .models import LaporanAkhir
        
        # Cek apakah laporan sudah ada untuk mahasiswa ini
        existing_laporan = LaporanAkhir.objects.filter(konfirmasi=konfirmasi).first()
        
        try:
            if existing_laporan:
                # Update existing
                existing_laporan.ringkasan_kegiatan = request.POST.get('ringkasan_kegiatan')
                existing_laporan.pencapaian = request.POST.get('pencapaian')
                existing_laporan.kendala_solusi = request.POST.get('kendala_solusi')
                existing_laporan.saran_perusahaan = request.POST.get('saran_perusahaan')
                existing_laporan.saran_kampus = request.POST.get('saran_kampus')
                existing_laporan.status = 'submitted'
                existing_laporan.submitted_at = timezone.now()
                existing_laporan.save()
                messages.success(request, 'Laporan akhir berhasil diperbarui.')
            else:
                # Create new
                laporan = LaporanAkhir.objects.create(
                    konfirmasi=konfirmasi,
                    ringkasan_kegiatan=request.POST.get('ringkasan_kegiatan'),
                    pencapaian=request.POST.get('pencapaian'),
                    kendala_solusi=request.POST.get('kendala_solusi'),
                    saran_perusahaan=request.POST.get('saran_perusahaan'),
                    saran_kampus=request.POST.get('saran_kampus'),
                    status='submitted',
                    submitted_at=timezone.now()
                )
                messages.success(request, 'Laporan akhir berhasil disimpan.')
                
            return redirect('coops:mahasiswa_dashboard')
            
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    # GET request - tampilkan form
    from .models import LaporanAkhir
    existing_laporan = LaporanAkhir.objects.filter(konfirmasi=konfirmasi).first()
    
    context = {
        'laporan': existing_laporan,
        'konfirmasi': konfirmasi
    }
    
    return render(request, 'coops/laporan_akhir_form.html', context)


@login_required
def evaluasi_supervisor(request, konfirmasi_id, template_id):
    """View untuk supervisor mengisi evaluasi mahasiswa"""
    from .models import EvaluasiTemplate, EvaluasiSupervisor
    import json
    
    try:
        konfirmasi = KonfirmasiMagang.objects.get(id=konfirmasi_id)
        template = EvaluasiTemplate.objects.get(id=template_id)
    except (KonfirmasiMagang.DoesNotExist, EvaluasiTemplate.DoesNotExist):
        messages.error(request, 'Data tidak ditemukan.')
        return redirect('/')
    
    # Get or create evaluation record
    evaluasi, created = EvaluasiSupervisor.objects.get_or_create(
        konfirmasi=konfirmasi,
        template=template,
        defaults={'status': 'pending'}
    )
    
    if request.method == 'POST':
        try:
            # Collect answers from form
            answers = {}
            for key, value in request.POST.items():
                if key.startswith('question_'):
                    question_id = key.replace('question_', '')
                    answers[question_id] = value
            
            # Save answers and update status
            evaluasi.jawaban = answers
            evaluasi.status = 'completed'
            evaluasi.submitted_at = timezone.now()
            evaluasi.save()
            
            messages.success(request, 'Evaluasi berhasil disimpan. Terima kasih atas partisipasi Anda.')
            return render(request, 'coops/evaluasi_success.html', {
                'konfirmasi': konfirmasi,
                'template': template
            })
            
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    # Parse questions from template
    try:
        questions = json.loads(template.pertanyaan) if template.pertanyaan else []
    except json.JSONDecodeError:
        questions = []
    
    # If evaluation already completed, show read-only view
    if evaluasi.status == 'completed':
        context = {
            'konfirmasi': konfirmasi,
            'template': template,
            'evaluasi': evaluasi,
            'questions': questions,
            'read_only': True
        }
        return render(request, 'coops/evaluasi_readonly.html', context)
    
    context = {
        'konfirmasi': konfirmasi,
        'template': template,
        'evaluasi': evaluasi,
        'questions': questions
    }
    
    return render(request, 'coops/evaluasi_form.html', context)


@login_required
def hasil_evaluasi(request, konfirmasi_id, template_id):
    """View untuk admin melihat hasil evaluasi yang sudah diisi"""
    if request.user.role != "admin":
        messages.error(request, "Akses ditolak. Anda bukan admin.")
        return redirect("/")
    
    from .models import EvaluasiTemplate, EvaluasiSupervisor
    import json
    
    try:
        konfirmasi = KonfirmasiMagang.objects.get(id=konfirmasi_id)
        template = EvaluasiTemplate.objects.get(id=template_id)
        evaluasi = EvaluasiSupervisor.objects.get(konfirmasi=konfirmasi, template=template)
    except (KonfirmasiMagang.DoesNotExist, EvaluasiTemplate.DoesNotExist, EvaluasiSupervisor.DoesNotExist):
        messages.error(request, 'Data evaluasi tidak ditemukan.')
        return redirect('coops:tracking_evaluasi')
    
    # Parse questions from template
    try:
        questions = json.loads(template.pertanyaan) if template.pertanyaan else []
    except json.JSONDecodeError:
        questions = []
    
    # Combine questions with answers
    qa_pairs = []
    for i, question in enumerate(questions):
        # Try to get answer by index first, then by key
        answer = None
        if evaluasi.jawaban:
            # Try numbered key first (standard format)
            answer = evaluasi.jawaban.get(str(i))
            if not answer:
                # Try direct index key
                answer = evaluasi.jawaban.get(i)
            if not answer:
                # If no numbered answers, check if it's a test/demo format
                if len(evaluasi.jawaban) == 1 and 'test' in evaluasi.jawaban:
                    answer = f"[Demo data] {evaluasi.jawaban.get('test', '')}"
                else:
                    # Try to find any answer for this question
                    answer = evaluasi.jawaban.get(f'jawaban_{i}', evaluasi.jawaban.get(f'question_{i}', 'Tidak dijawab'))
        
        if not answer:
            answer = 'Tidak dijawab'
            
        qa_pairs.append({
            'question': question,
            'answer': answer
        })
    
    context = {
        'konfirmasi': konfirmasi,
        'template': template,
        'evaluasi': evaluasi,
        'qa_pairs': qa_pairs
    }
    
    return render(request, 'coops/hasil_evaluasi.html', context)


@login_required
def daftar_laporan_kemajuan(request):
    """View untuk admin melihat daftar semua laporan kemajuan mahasiswa"""
    if request.user.role != "admin":
        messages.error(request, "Akses ditolak. Anda bukan admin.")
        return redirect("/")
        
    from .models import LaporanKemajuan
    from accounts.models import Mahasiswa
    
    # Get all laporan kemajuan with related konfirmasi data
    laporan_list = LaporanKemajuan.objects.select_related('konfirmasi__mahasiswa').order_by('-created_at')
    
    # Get list of mahasiswa who have accepted internships but haven't submitted reports
    submitted_konfirmasi_ids = laporan_list.values_list('konfirmasi_id', flat=True)
    konfirmasi_belum_submit = KonfirmasiMagang.objects.filter(
        status='accepted'
    ).exclude(id__in=submitted_konfirmasi_ids).select_related('mahasiswa')
    
    context = {
        'laporan_list': laporan_list,
        'konfirmasi_belum_submit': konfirmasi_belum_submit,
        'total_mahasiswa_magang': KonfirmasiMagang.objects.filter(status='accepted').count(),
        'total_submitted': laporan_list.count(),
    }
    
    return render(request, 'coops/daftar_laporan_kemajuan.html', context)


@login_required
def laporan_mahasiswa(request):
    """View untuk mahasiswa melihat daftar laporan kemajuan mereka sendiri"""
    if request.user.role != "mahasiswa":
        messages.error(request, "Akses ditolak. Anda bukan mahasiswa.")
        return redirect("/")
        
    try:
        mahasiswa = Mahasiswa.objects.get(email=request.user)
        konfirmasi = KonfirmasiMagang.objects.get(mahasiswa=request.user)
        
        if konfirmasi.status not in ['accepted', 'completed']:
            messages.warning(request, "Anda belum memiliki magang yang disetujui.")
            return redirect('coops:mahasiswa_dashboard')
            
        laporan_list = LaporanKemajuan.objects.filter(konfirmasi=konfirmasi).order_by('-created_at')
        
        context = {
            'laporan_list': laporan_list,
            'konfirmasi': konfirmasi,
            'mahasiswa': mahasiswa,
            'total_laporan': laporan_list.count(),
        }
        
        return render(request, 'coops/laporan_mahasiswa.html', context)
        
    except Mahasiswa.DoesNotExist:
        messages.error(request, "Data mahasiswa tidak ditemukan. Silakan hubungi admin.")
        return redirect('coops:mahasiswa_dashboard')
    except KonfirmasiMagang.DoesNotExist:
        messages.warning(request, "Anda belum mengajukan konfirmasi magang.")
        return redirect('coops:mahasiswa_dashboard')


@login_required
def kirim_ke_kaprodi(request, template_id):
    """View untuk admin mengirim hasil evaluasi ke Kaprodi dan Mentor"""
    if request.user.role != "admin":
        messages.error(request, "Akses ditolak. Anda bukan admin.")
        return redirect("/")
    
    if request.method != 'POST':
        messages.error(request, "Method tidak diizinkan.")
        return redirect('coops:tracking_evaluasi')
    
    from .models import EvaluasiTemplate, EvaluasiSupervisor
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    import json
    
    try:
        template = EvaluasiTemplate.objects.get(id=template_id)
    except EvaluasiTemplate.DoesNotExist:
        messages.error(request, 'Template evaluasi tidak ditemukan.')
        return redirect('coops:tracking_evaluasi')
    
    # Get all completed evaluations for this template
    completed_evaluations = EvaluasiSupervisor.objects.filter(
        template=template, 
        status='completed'
    ).select_related('konfirmasi__mahasiswa')
    
    if not completed_evaluations.exists():
        messages.error(request, 'Tidak ada evaluasi yang sudah diselesaikan untuk template ini.')
        return redirect('coops:tracking_evaluasi')
    
    # Prepare email content
    try:
        # Parse questions for better email formatting
        questions = json.loads(template.pertanyaan) if template.pertanyaan else []
        
        # Prepare evaluation summary data
        evaluation_summary = []
        for evaluasi in completed_evaluations:
            # Combine questions with answers
            qa_pairs = []
            for i, question in enumerate(questions):
                answer = 'Tidak dijawab'
                if evaluasi.jawaban:
                    answer = evaluasi.jawaban.get(str(i)) or evaluasi.jawaban.get(i) or 'Tidak dijawab'
                
                qa_pairs.append({
                    'question': question,
                    'answer': answer
                })
            
            evaluation_summary.append({
                'mahasiswa': evaluasi.konfirmasi.mahasiswa,
                'supervisor': evaluasi.konfirmasi.nama_supervisor,
                'perusahaan': evaluasi.konfirmasi.nama_perusahaan,
                'posisi': evaluasi.konfirmasi.posisi,
                'submitted_at': evaluasi.submitted_at,
                'qa_pairs': qa_pairs
            })
        
        # Email context
        email_context = {
            'template': template,
            'evaluation_summary': evaluation_summary,
            'total_evaluations': completed_evaluations.count(),
            'admin_user': request.user
        }
        
        # Render email templates
        subject = f'Hasil Evaluasi {template.get_jenis_display()} - {template.nama}'
        html_message = render_to_string('coops/email_hasil_evaluasi.html', email_context)
        plain_message = strip_tags(html_message)
        
        # Email addresses (you should configure these in settings or as admin preferences)
        kaprodi_email = getattr(settings, 'KAPRODI_EMAIL', 'kaprodi@university.edu')
        mentor_email = getattr(settings, 'MENTOR_EMAIL', 'mentor@university.edu')
        
        recipient_list = [kaprodi_email, mentor_email]
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False
        )
        
        # Mark template as sent (you might want to add a field to track this)
        # For now, we'll just show success message
        messages.success(request, 
            f'Hasil evaluasi {template.nama} berhasil dikirim ke Kaprodi dan Mentor. '
            f'Total {completed_evaluations.count()} evaluasi telah dikirim.')
        
    except Exception as e:
        messages.error(request, f'Gagal mengirim email: {str(e)}')
    
    return redirect('coops:tracking_evaluasi')


@login_required
def sertifikat_coop(request):
    """View untuk mahasiswa melihat/download sertifikat coop"""
    if request.user.role != "mahasiswa":
        messages.error(request, "Akses ditolak. Anda bukan mahasiswa.")
        return redirect("/")
    
    try:
        konfirmasi = KonfirmasiMagang.objects.get(mahasiswa=request.user, status='completed')
    except KonfirmasiMagang.DoesNotExist:
        messages.error(request, 'Anda belum menyelesaikan program coop atau status belum diubah ke completed.')
        return redirect('coops:mahasiswa_dashboard')
    
    # Get or create certificate
    from .models import SertifikatCoop
    sertifikat, created = SertifikatCoop.objects.get_or_create(
        konfirmasi=konfirmasi,
        defaults={
            'nilai_akhir': 'A',  # Default grade, should be set by admin
            'status': 'issued'
        }
    )
    
    # Get mahasiswa data
    try:
        mahasiswa_obj = request.user.mahasiswa
    except:
        mahasiswa_obj = None
    
    context = {
        'sertifikat': sertifikat,
        'konfirmasi': konfirmasi,
        'mahasiswa': mahasiswa_obj
    }
    
    return render(request, 'coops/sertifikat_coop.html', context)


@login_required
def generate_sertifikat(request, konfirmasi_id):
    """View untuk admin generate sertifikat untuk mahasiswa yang sudah completed"""
    if request.user.role != "admin":
        messages.error(request, "Akses ditolak. Anda bukan admin.")
        return redirect("/")
    
    try:
        konfirmasi = KonfirmasiMagang.objects.get(id=konfirmasi_id, status='completed')
    except KonfirmasiMagang.DoesNotExist:
        messages.error(request, 'Konfirmasi magang tidak ditemukan atau belum completed.')
        return redirect('coops:status_magang')
    
    if request.method == 'POST':
        nilai_akhir = request.POST.get('nilai_akhir', 'A')
        
        from .models import SertifikatCoop
        sertifikat, created = SertifikatCoop.objects.get_or_create(
            konfirmasi=konfirmasi,
            defaults={
                'nilai_akhir': nilai_akhir,
                'dikeluarkan_oleh': request.user,
                'status': 'issued'
            }
        )
        
        if not created:
            # Update existing certificate
            sertifikat.nilai_akhir = nilai_akhir
            sertifikat.dikeluarkan_oleh = request.user
            sertifikat.status = 'issued'
            sertifikat.save()
        
        messages.success(request, f'Sertifikat berhasil diterbitkan untuk {konfirmasi.mahasiswa.get_full_name()}')
        return redirect('coops:status_magang')
    
    # GET request - show form
    try:
        mahasiswa_obj = konfirmasi.mahasiswa.mahasiswa
    except:
        mahasiswa_obj = None
    
    context = {
        'konfirmasi': konfirmasi,
        'mahasiswa': mahasiswa_obj
    }
    
    return render(request, 'coops/generate_sertifikat.html', context)


# Weekly Report Views
@login_required
def weekly_report(request):
    """View untuk mahasiswa membuat laporan mingguan"""
    if request.user.role != "mahasiswa":
        messages.error(request, "Akses ditolak. Anda bukan mahasiswa.")
        return redirect("/")
    
    from .models import WeeklyReport, DeadlineReminder, KonfirmasiMagang
    from .forms import WeeklyReportForm
    from django.utils import timezone
    
    # Check if mahasiswa has confirmed internship
    has_internship = KonfirmasiMagang.objects.filter(
        mahasiswa__nama=request.user,
        status='accepted'
    ).exists()
    
    if has_internship:
        messages.info(request, "Anda sudah mendapat tempat magang dan tidak perlu membuat laporan mingguan.")
        return redirect('coops:mahasiswa_dashboard')
    
    # Check if there's active deadline
    active_deadline = DeadlineReminder.objects.filter(is_active=True).first()
    
    if not active_deadline:
        messages.warning(request, "Deadline magang belum diatur. Silakan hubungi admin.")
        return redirect('coops:mahasiswa_dashboard')
    
    # Check if deadline has passed
    today = timezone.now().date()
    if today <= active_deadline.deadline_date:
        messages.info(request, "Deadline magang belum terlewati. Laporan mingguan belum diperlukan.")
        return redirect('coops:mahasiswa_dashboard')
    
    # Get current week start (Monday)
    days_since_monday = today.weekday()
    current_week_start = today - timezone.timedelta(days=days_since_monday)
    current_week_end = current_week_start + timezone.timedelta(days=6)
    
    # Calculate week number since deadline
    weeks_since_deadline = ((current_week_start - active_deadline.deadline_date).days // 7) + 1
    
    # Check if report already exists for this week
    existing_report = WeeklyReport.objects.filter(
        student=request.user,
        week_start_date=current_week_start
    ).first()
    
    if request.method == 'POST':
        if existing_report:
            form = WeeklyReportForm(request.POST, instance=existing_report)
        else:
            form = WeeklyReportForm(request.POST)
            
        if form.is_valid():
            report = form.save(commit=False)
            report.student = request.user
            report.week_start_date = current_week_start
            report.week_end_date = current_week_end
            report.week_number = weeks_since_deadline
            
            # Check if submitted late
            if today > current_week_end:
                report.is_late = True
                
            report.save()
            
            messages.success(request, "Laporan mingguan berhasil disimpan.")
            return redirect('coops:weekly_report_list')
    else:
        if existing_report:
            form = WeeklyReportForm(instance=existing_report)
        else:
            form = WeeklyReportForm()
    
    context = {
        'form': form,
        'week_start': current_week_start,
        'week_end': current_week_end,
        'week_number': weeks_since_deadline,
        'existing_report': existing_report,
        'active_deadline': active_deadline,
    }
    
    return render(request, 'coops/weekly_report.html', context)


@login_required
def weekly_report_list(request):
    """View untuk melihat daftar laporan mingguan mahasiswa"""
    if request.user.role != "mahasiswa":
        messages.error(request, "Akses ditolak. Anda bukan mahasiswa.")
        return redirect("/")
    
    from .models import WeeklyReport, DeadlineReminder
    from django.utils import timezone
    
    # Get active deadline
    active_deadline = DeadlineReminder.objects.filter(is_active=True).first()
    
    reports = WeeklyReport.objects.filter(student=request.user).order_by('-week_start_date')
    
    # Check if current week report is needed
    today = timezone.now().date()
    days_since_monday = today.weekday()
    current_week_start = today - timezone.timedelta(days=days_since_monday)
    
    current_week_report = WeeklyReport.objects.filter(
        student=request.user,
        week_start_date=current_week_start
    ).first()
    
    need_current_report = False
    if active_deadline and today > active_deadline.deadline_date and not current_week_report:
        need_current_report = True
    
    context = {
        'reports': reports,
        'active_deadline': active_deadline,
        'current_week_start': current_week_start,
        'current_week_report': current_week_report,
        'need_current_report': need_current_report,
        'total_reports': reports.count(),
    }
    
    return render(request, 'coops/weekly_report_list.html', context)


@login_required
def admin_weekly_reports(request):
    """View untuk admin melihat semua laporan mingguan"""
    if request.user.role != "admin":
        messages.error(request, "Akses ditolak. Anda bukan admin.")
        return redirect("/")
    
    from .models import WeeklyReport, DeadlineReminder, KonfirmasiMagang
    from accounts.models import User
    from django.utils import timezone
    
    # Get all weekly reports
    reports = WeeklyReport.objects.select_related('student').order_by('-week_start_date', 'student__username')
    
    # Get active deadline settings
    active_deadline = DeadlineReminder.objects.filter(is_active=True).first()
    
    # Get mahasiswa who need to submit but haven't
    overdue_mahasiswa = []
    
    if active_deadline:
        today = timezone.now().date()
        
        # Get mahasiswa yang belum mendapat tempat magang (tidak ada konfirmasi yang accepted)
        mahasiswa_without_internship = User.objects.filter(
            role='mahasiswa'
        ).exclude(
            konfirmasimagang__status='accepted'
        )
        
        # Cek yang melewati deadline
        if today > active_deadline.deadline_date:
            days_since_monday = today.weekday()
            current_week_start = today - timezone.timedelta(days=days_since_monday)
            
            for mahasiswa in mahasiswa_without_internship:
                # Cek apakah sudah submit laporan minggu ini
                current_report = WeeklyReport.objects.filter(
                    student=mahasiswa,
                    week_start_date=current_week_start
                ).first()
                
                if not current_report:
                    overdue_mahasiswa.append({
                        'mahasiswa': mahasiswa,
                        'deadline': active_deadline.deadline_date,
                        'days_overdue': (today - active_deadline.deadline_date).days
                    })
    
    context = {
        'reports': reports,
        'overdue_mahasiswa': overdue_mahasiswa,
        'active_deadline': active_deadline,
        'total_reports': reports.count(),
        'total_overdue': len(overdue_mahasiswa),
    }
    
    return render(request, 'coops/admin_weekly_reports.html', context)


@login_required
def manage_deadline_reminder(request):
    """View untuk admin mengatur deadline dan reminder global"""
    if request.user.role != "admin":
        messages.error(request, "Akses ditolak. Anda bukan admin.")
        return redirect("/")
    
    from .models import DeadlineReminder, WeeklyReport
    from .forms import DeadlineReminderForm
    from django.utils import timezone
    
    # Get active deadline or create new one
    active_deadline = DeadlineReminder.objects.filter(is_active=True).first()
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'create':
            # Create new deadline
            form = DeadlineReminderForm(request.POST)
            if form.is_valid():
                deadline = form.save(commit=False)
                # Deactivate other deadlines first
                DeadlineReminder.objects.update(is_active=False)
                # Set this one as active
                deadline.is_active = True
                deadline.save()
                messages.success(request, "Deadline baru berhasil dibuat dan diaktifkan.")
                return redirect('coops:manage_deadline_reminder')
            else:
                messages.error(request, "Gagal membuat deadline. Periksa data yang dimasukkan.")
                
        elif action == 'update' and active_deadline:
            # Update existing deadline
            form = DeadlineReminderForm(request.POST, instance=active_deadline)
            if form.is_valid():
                form.save()
                messages.success(request, "Pengaturan deadline berhasil diperbarui.")
                return redirect('coops:manage_deadline_reminder')
            else:
                messages.error(request, "Gagal memperbarui deadline. Periksa data yang dimasukkan.")
                
        elif action == 'activate':
            # Activate a specific deadline
            reminder_id = request.POST.get('reminder_id')
            if reminder_id:
                try:
                    # Deactivate all first
                    DeadlineReminder.objects.update(is_active=False)
                    # Activate selected one
                    reminder = DeadlineReminder.objects.get(id=reminder_id)
                    reminder.is_active = True
                    reminder.save()
                    messages.success(request, "Deadline berhasil diaktifkan.")
                except DeadlineReminder.DoesNotExist:
                    messages.error(request, "Deadline tidak ditemukan.")
                return redirect('coops:manage_deadline_reminder')
                
        elif action == 'deactivate':
            # Deactivate a specific deadline
            reminder_id = request.POST.get('reminder_id')
            if reminder_id:
                try:
                    reminder = DeadlineReminder.objects.get(id=reminder_id)
                    reminder.is_active = False
                    reminder.save()
                    messages.success(request, "Deadline berhasil dinonaktifkan.")
                except DeadlineReminder.DoesNotExist:
                    messages.error(request, "Deadline tidak ditemukan.")
                return redirect('coops:manage_deadline_reminder')
        
        else:
            # Default form handling (backward compatibility)
            if active_deadline:
                form = DeadlineReminderForm(request.POST, instance=active_deadline)
            else:
                form = DeadlineReminderForm(request.POST)
                
            if form.is_valid():
                deadline = form.save(commit=False)
                
                # Deactivate other deadlines first
                DeadlineReminder.objects.update(is_active=False)
                
                # Set this one as active
                deadline.is_active = True
                deadline.save()
                
                messages.success(request, "Deadline berhasil disimpan dan diaktifkan.")
                return redirect('coops:admin_weekly_reports')
    else:
        if active_deadline:
            form = DeadlineReminderForm(instance=active_deadline)
        else:
            form = DeadlineReminderForm(initial={
                'deadline_date': timezone.now().date() + timezone.timedelta(days=30),
                'reminder_frequency_days': 7,
                'description': 'Deadline pencarian tempat magang',
                'email_reminder_enabled': True,
                'is_active': True,
            })
    
    # Get all deadline history
    all_deadlines = DeadlineReminder.objects.all().order_by('-created_at')
    
    # Calculate statistics if there's an active deadline
    stats = {}
    if active_deadline:
        from accounts.models import Mahasiswa
        from datetime import date
        
        # Count total students
        total_students = Mahasiswa.objects.count()
        
        # Calculate days until deadline
        days_until = (active_deadline.deadline_date - date.today()).days
        
        # Count overdue students (students who passed deadline but haven't found internship)
        overdue_students = Mahasiswa.objects.filter(
            konfirmasimagang__isnull=True
        ).count() if days_until < 0 else 0
        
        # Count weekly reports this week
        from datetime import datetime, timedelta
        week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
        weekly_reports_count = WeeklyReport.objects.filter(
            submitted_at__date__gte=week_start
        ).count()
        
        # Get recent reports
        recent_reports = WeeklyReport.objects.select_related('student').order_by('-submitted_at')[:5]
        
        stats = {
            'total_affected_students': total_students,
            'days_until_deadline': max(0, days_until),
            'overdue_students': overdue_students,
            'weekly_reports_count': weekly_reports_count,
            'recent_reports': recent_reports,
        }
    
    context = {
        'form': form,
        'active_deadline': active_deadline,
        'current_reminder': active_deadline,  # Add this for template compatibility
        'all_deadlines': all_deadlines,
        **stats  # Spread the stats dictionary
    }

    return render(request, 'coops/manage_deadline_reminder.html', context)

@login_required
def get_notifications(request):
    """Get notifications for the current user"""
    from django.http import JsonResponse
    from .models import Notification

    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]

    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'type': notif.notification_type,
            'is_read': notif.is_read,
            'link': notif.link or '',
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count,
    })

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    from django.http import JsonResponse
    from .models import Notification

    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    from django.http import JsonResponse
    from .models import Notification

    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def download_sertifikat(request, sertifikat_id):
    """Download certificate as PDF"""
    from django.http import FileResponse
    from .models import SertifikatCoop
    from .certificate_generator import CertificateGenerator

    try:
        sertifikat = SertifikatCoop.objects.get(id=sertifikat_id)

        if request.user.role == 'mahasiswa' and sertifikat.konfirmasi.mahasiswa != request.user:
            messages.error(request, "Anda tidak memiliki akses ke sertifikat ini.")
            return redirect('coops:mahasiswa_dashboard')

        generator = CertificateGenerator(sertifikat)
        pdf_buffer = generator.generate_pdf()

        filename = f"Sertifikat_COOP_{sertifikat.nomor_sertifikat.replace('/', '_')}.pdf"

        response = FileResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except SertifikatCoop.DoesNotExist:
        messages.error(request, "Sertifikat tidak ditemukan.")
        return redirect('coops:mahasiswa_dashboard')
