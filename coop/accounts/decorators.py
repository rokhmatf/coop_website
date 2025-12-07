from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(required_role):
    """
    Decorator untuk memastikan user memiliki role yang tepat
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if request.user.role != required_role:
                messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
                return redirect('accounts:login')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def mahasiswa_required(view_func):
    """Decorator khusus untuk view yang hanya bisa diakses mahasiswa"""
    return role_required('mahasiswa')(view_func)

def admin_required(view_func):
    """Decorator khusus untuk view yang hanya bisa diakses admin"""
    return role_required('admin')(view_func)

def supervisor_required(view_func):
    """Decorator khusus untuk view yang hanya bisa diakses supervisor"""
    return role_required('supervisor')(view_func)