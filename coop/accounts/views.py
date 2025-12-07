from django.contrib.auth.views import LoginView
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from .models import User, Mahasiswa, Kaprodi
from .forms import CustomLoginForm, SupervisorRegistrationForm, KaprodiRegistrationForm
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth.decorators import login_required
from .decorators import admin_required, kaprodi_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import update_session_auth_hash

class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = CustomLoginForm

    def form_valid(self, form):
        user = form.cleaned_data.get('user')
        login(self.request, user)

        if user.must_change_password:
            return redirect(reverse("accounts:force_password_change"))

        if user.role == "mahasiswa":
            return redirect(reverse("coops:mahasiswa_dashboard"))
        elif user.role == "supervisor":
            return redirect(reverse("jobs:supervisor_dashboard"))
        elif user.role == "admin":
            return redirect(reverse("coops:status_magang"))
        elif user.role == "kaprodi":
            return redirect(reverse("accounts:kaprodi_dashboard"))
        return redirect("/")

    def form_invalid(self, form):
        return super().form_invalid(form)

@login_required
@admin_required
def register_supervisor(request):
    if request.method == 'POST':
        form = SupervisorRegistrationForm(request.POST)
        if form.is_valid():
            try:
                supervisor = form.save()
                messages.success(request, f'Supervisor {supervisor.get_full_name()} berhasil didaftarkan.')
                return redirect('accounts:register_supervisor')
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {str(e)}')
        else:
            messages.error(request, 'Mohon perbaiki kesalahan pada form.')
    else:
        form = SupervisorRegistrationForm()

    # Get list of existing supervisors
    supervisors = User.objects.filter(role='supervisor').order_by('-date_joined')

    context = {
        'form': form,
        'supervisors': supervisors,
        'title': 'Registrasi Supervisor'
    }
    return render(request, 'accounts/register_supervisor.html', context)


@login_required
@admin_required
def register_kaprodi(request):
    if request.method == 'POST':
        form = KaprodiRegistrationForm(request.POST)
        if form.is_valid():
            try:
                kaprodi_user = form.save()
                messages.success(request, f'Kaprodi {kaprodi_user.kaprodi_profile.nama} berhasil didaftarkan.')
                return redirect('accounts:register_kaprodi')
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {str(e)}')
        else:
            messages.error(request, 'Mohon perbaiki kesalahan pada form.')
    else:
        form = KaprodiRegistrationForm()

    # Get list of existing kaprodi
    kaprodis = Kaprodi.objects.all().order_by('-created_at')

    context = {
        'form': form,
        'kaprodis': kaprodis,
        'title': 'Registrasi Kaprodi'
    }
    return render(request, 'accounts/register_kaprodi.html', context)
    
def register(request):
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "register":
            email = request.POST.get("email")
            password = request.POST.get("password")
            nama_lengkap = request.POST.get("nama")

            # Prevent duplicate usernames/emails
            if User.objects.filter(username=email).exists():
                messages.error(request, "Email sudah terdaftar. Silakan gunakan email lain atau login.")
                return render(request, "accounts/register.html")

            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=password,
                        role="mahasiswa"
                    )

                    # store full name on the User record as-is
                    if nama_lengkap:
                        user.first_name = nama_lengkap.strip()
                        user.save()

                    # Create Mahasiswa record linking to the created user
                    Mahasiswa.objects.create(
                        nama=nama_lengkap,
                        nim=request.POST.get("nim"),
                        prodi=request.POST.get("prodi"),
                        angkatan=int(request.POST.get("angkatan")) if request.POST.get("angkatan") else None,
                        jenis_kelamin=request.POST.get("jenis_kelamin"),
                        konsultasi=request.POST.get("konsultasi", ""),
                        sptjm=request.POST.get("sptjm", ""),
                        email=user,
                        no_hp=request.POST.get("no_hp"),
                        porto=request.POST.get("porto", ""),
                        cv=request.POST.get("cv", "")
                    )

                messages.success(request, "Registrasi berhasil! Silakan masuk.")
                return redirect("accounts:login")
            except IntegrityError:
                messages.error(request, "Terjadi kesalahan pada server saat membuat akun. Silakan coba lagi.")
                return render(request, "accounts/register.html")
        else:
            messages.error(request, "Terjadi kesalahan saat registrasi. Silakan coba lagi.")
    return render(request, "accounts/register.html")


@login_required
def custom_logout(request):
    """Custom logout view with better UX"""
    if request.method == 'POST':
        user_name = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'Anda telah berhasil logout. Sampai jumpa, {user_name}!')
        return redirect('accounts:login')

    # GET request - show confirmation
    return render(request, 'accounts/logout_confirm.html')


def supervisor_password_reset_confirm(request, uidb64, token):
    """
    Handle password reset confirmation for supervisors.
    Validates token and allows setting new password.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')

            if not password or len(password) < 8:
                messages.error(request, 'Password harus minimal 8 karakter.')
                return render(request, 'accounts/password_reset_confirm.html', {'validlink': True})

            if password != password_confirm:
                messages.error(request, 'Password dan konfirmasi password tidak sama.')
                return render(request, 'accounts/password_reset_confirm.html', {'validlink': True})

            user.set_password(password)
            user.must_change_password = False
            user.save()

            messages.success(request, 'Password berhasil diatur! Silakan login dengan password baru Anda.')
            return redirect('accounts:login')

        return render(request, 'accounts/password_reset_confirm.html', {'validlink': True})
    else:
        messages.error(request, 'Link reset password tidak valid atau sudah kadaluarsa.')
        return render(request, 'accounts/password_reset_confirm.html', {'validlink': False})


@login_required
def force_password_change(request):
    """
    Force supervisor to change password on first login.
    This view is called when must_change_password is True.
    """
    if not request.user.must_change_password:
        if request.user.role == 'supervisor':
            return redirect('jobs:supervisor_dashboard')
        elif request.user.role == 'mahasiswa':
            return redirect('coops:mahasiswa_dashboard')
        return redirect('/')

    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or len(new_password) < 8:
            messages.error(request, 'Password baru harus minimal 8 karakter.')
            return render(request, 'accounts/force_password_change.html')

        if new_password != confirm_password:
            messages.error(request, 'Password baru dan konfirmasi password tidak sama.')
            return render(request, 'accounts/force_password_change.html')

        request.user.set_password(new_password)
        request.user.must_change_password = False
        request.user.save()

        update_session_auth_hash(request, request.user)

        messages.success(request, 'Password berhasil diubah! Anda sekarang dapat menggunakan sistem.')

        if request.user.role == 'supervisor':
            return redirect('jobs:supervisor_dashboard')
        elif request.user.role == 'mahasiswa':
            return redirect('coops:mahasiswa_dashboard')
        return redirect('/')

    return render(request, 'accounts/force_password_change.html')


@login_required
@kaprodi_required
def kaprodi_dashboard(request):
    """Dashboard monitoring untuk Kaprodi"""
    from coops.models import KonfirmasiMagang
    from django.db.models import Q, Count

    kaprodi = request.user.kaprodi_profile

    # Get all mahasiswa from the same jurusan
    mahasiswa_jurusan = Mahasiswa.objects.filter(jurusan=kaprodi.jurusan)

    # Get all konfirmasi magang for mahasiswa in this jurusan
    konfirmasi_jurusan = KonfirmasiMagang.objects.filter(
        mahasiswa__mahasiswa__jurusan=kaprodi.jurusan
    ).select_related('mahasiswa', 'mahasiswa__mahasiswa', 'approved_by')

    # Statistics
    total_mahasiswa = mahasiswa_jurusan.count()

    # Count by status
    pending_count = konfirmasi_jurusan.filter(status='pending').count()
    accepted_count = konfirmasi_jurusan.filter(status='accepted').count()
    rejected_count = konfirmasi_jurusan.filter(status='rejected').count()
    completed_count = konfirmasi_jurusan.filter(status='completed').count()

    # Mahasiswa yang belum ada konfirmasi magang
    mahasiswa_with_konfirmasi = konfirmasi_jurusan.values_list('mahasiswa__id', flat=True)
    mahasiswa_tanpa_magang = mahasiswa_jurusan.exclude(email__id__in=mahasiswa_with_konfirmasi).count()

    # Recent activities (last 10 status changes)
    recent_konfirmasi = konfirmasi_jurusan.order_by('-updated_at')[:10]

    # Filter parameters
    filter_status = request.GET.get('status', '')
    filter_angkatan = request.GET.get('angkatan', '')
    search_query = request.GET.get('search', '')

    # Build filtered mahasiswa list
    mahasiswa_list = mahasiswa_jurusan

    if filter_angkatan:
        mahasiswa_list = mahasiswa_list.filter(angkatan=filter_angkatan)

    if search_query:
        mahasiswa_list = mahasiswa_list.filter(
            Q(nama__icontains=search_query) |
            Q(nim__icontains=search_query)
        )

    # Prepare mahasiswa data with their konfirmasi status
    mahasiswa_data = []
    for mhs in mahasiswa_list:
        try:
            konfirmasi = KonfirmasiMagang.objects.filter(mahasiswa=mhs.email).first()

            # Apply status filter
            if filter_status:
                if not konfirmasi or konfirmasi.status != filter_status:
                    if filter_status != 'none' or konfirmasi:
                        continue

            mahasiswa_data.append({
                'mahasiswa': mhs,
                'konfirmasi': konfirmasi
            })
        except Exception:
            # If no konfirmasi, add if filter is 'none' or no filter
            if not filter_status or filter_status == 'none':
                mahasiswa_data.append({
                    'mahasiswa': mhs,
                    'konfirmasi': None
                })

    # Get unique angkatan for filter dropdown
    angkatan_list = mahasiswa_jurusan.values_list('angkatan', flat=True).distinct().order_by('-angkatan')

    context = {
        'kaprodi': kaprodi,
        'title': 'Dashboard Kaprodi',
        'total_mahasiswa': total_mahasiswa,
        'pending_count': pending_count,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
        'completed_count': completed_count,
        'mahasiswa_tanpa_magang': mahasiswa_tanpa_magang,
        'mahasiswa_data': mahasiswa_data,
        'recent_konfirmasi': recent_konfirmasi,
        'angkatan_list': angkatan_list,
        'filter_status': filter_status,
        'filter_angkatan': filter_angkatan,
        'search_query': search_query,
    }
    return render(request, 'accounts/kaprodi_dashboard.html', context)
