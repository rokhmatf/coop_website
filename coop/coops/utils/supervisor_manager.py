from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from accounts.models import User
from jobs.models import Supervisor
import logging

logger = logging.getLogger(__name__)


def create_supervisor_with_reset_link(email_supervisor, nama_supervisor, wa_supervisor, nama_perusahaan, bidang_usaha):
    """
    Create or get supervisor account and generate reset password token.

    Args:
        email_supervisor: Email of the supervisor
        nama_supervisor: Full name of the supervisor
        wa_supervisor: WhatsApp number of the supervisor
        nama_perusahaan: Company name
        bidang_usaha: Business field/industry

    Returns:
        tuple: (user_object, is_new, reset_token, uidb64)
            - user_object: The User instance
            - is_new: Boolean indicating if the account was newly created
            - reset_token: Password reset token
            - uidb64: Base64 encoded user ID
    """
    try:
        user = User.objects.get(email=email_supervisor, role='supervisor')
        is_new = False
        logger.info(f"Supervisor existing account found: {email_supervisor}")

        supervisor_profile = user.supervisor_profile
        if nama_perusahaan and not supervisor_profile.perusahaan:
            supervisor_profile.perusahaan = nama_perusahaan
        if bidang_usaha and not supervisor_profile.bidang_usaha:
            supervisor_profile.bidang_usaha = bidang_usaha
        if wa_supervisor and not supervisor_profile.no_hp:
            supervisor_profile.no_hp = wa_supervisor
        supervisor_profile.save()

    except User.DoesNotExist:
        user = User.objects.create(
            username=email_supervisor,
            email=email_supervisor,
            role='supervisor',
            must_change_password=True,
            first_name=nama_supervisor
        )
        user.set_unusable_password()
        user.save()

        Supervisor.objects.create(
            user=user,
            nama=nama_supervisor,
            email=email_supervisor,
            no_hp=wa_supervisor or '',
            perusahaan=nama_perusahaan or '',
            bidang_usaha=bidang_usaha or '',
            created_automatically=True
        )

        is_new = True
        logger.info(f"New supervisor account created: {email_supervisor}")

    except User.MultipleObjectsReturned:
        logger.error(f"Multiple users found with email {email_supervisor}")
        user = User.objects.filter(email=email_supervisor, role='supervisor').first()
        is_new = False

    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

    return user, is_new, token, uidb64
