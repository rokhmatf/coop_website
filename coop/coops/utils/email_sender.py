from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_supervisor_welcome_email(supervisor_user, reset_url, mahasiswa_info):
    """
    Send welcome email to new supervisor with password reset link.

    Args:
        supervisor_user: The User instance of the supervisor
        reset_url: Full URL for password reset
        mahasiswa_info: Dictionary containing mahasiswa information:
            - nama: Student name
            - prodi: Study program
            - periode_awal: Start date
            - periode_akhir: End date
            - posisi: Position
            - nama_perusahaan: Company name

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        subject = 'Akun Supervisor - Sistem Magang Prasetiya Mulya'

        context = {
            'nama_supervisor': supervisor_user.first_name or supervisor_user.username,
            'username': supervisor_user.email,
            'reset_url': reset_url,
            'mahasiswa': mahasiswa_info,
            'kaprodi_email': settings.KAPRODI_EMAIL,
        }

        html_content = render_to_string('accounts/emails/supervisor_welcome.html', context)
        text_content = render_to_string('accounts/emails/supervisor_welcome.txt', context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[supervisor_user.email]
        )

        email.attach_alternative(html_content, "text/html")

        email.send(fail_silently=False)

        logger.info(f"Welcome email sent successfully to {supervisor_user.email}")
        return True, None

    except Exception as e:
        error_msg = f"Failed to send email to {supervisor_user.email}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
