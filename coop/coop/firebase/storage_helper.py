"""
Firebase Storage Helper Functions
Handles file upload, download, and management with Firebase Storage
"""

import firebase_admin
from firebase_admin import credentials, storage
from django.conf import settings
import os
import uuid
from datetime import timedelta


def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    if not firebase_admin._apps:
        cred_dict = {
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
            "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "client_id": settings.FIREBASE_CLIENT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": settings.FIREBASE_CERT_URL
        }

        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': settings.FIREBASE_STORAGE_BUCKET
        })


def upload_file_to_firebase(file, folder='uploads', filename=None):
    """
    Upload a file to Firebase Storage

    Args:
        file: Django UploadedFile object
        folder: Folder path in Firebase Storage (default: 'uploads')
        filename: Custom filename (optional, will use original or generate UUID)

    Returns:
        str: Public URL of the uploaded file
    """
    try:
        initialize_firebase()

        bucket = storage.bucket()

        if filename is None:
            ext = os.path.splitext(file.name)[1]
            filename = f"{uuid.uuid4()}{ext}"

        blob_path = f"{folder}/{filename}"
        blob = bucket.blob(blob_path)

        blob.upload_from_file(file, content_type=file.content_type)

        blob.make_public()

        return blob.public_url

    except Exception as e:
        print(f"Error uploading file to Firebase: {str(e)}")
        return None


def upload_cv(file, mahasiswa_nim):
    """
    Upload CV file to Firebase Storage

    Args:
        file: Django UploadedFile object
        mahasiswa_nim: Student NIM for organizing files

    Returns:
        str: Public URL of the uploaded CV
    """
    filename = f"cv_{mahasiswa_nim}{os.path.splitext(file.name)[1]}"
    return upload_file_to_firebase(file, folder='cvs', filename=filename)


def upload_portfolio(file, mahasiswa_nim):
    """
    Upload portfolio file to Firebase Storage

    Args:
        file: Django UploadedFile object
        mahasiswa_nim: Student NIM for organizing files

    Returns:
        str: Public URL of the uploaded portfolio
    """
    filename = f"portfolio_{mahasiswa_nim}{os.path.splitext(file.name)[1]}"
    return upload_file_to_firebase(file, folder='portfolios', filename=filename)


def upload_surat_penerimaan(file, mahasiswa_nim, company_name):
    """
    Upload acceptance letter to Firebase Storage

    Args:
        file: Django UploadedFile object
        mahasiswa_nim: Student NIM
        company_name: Company name for organizing files

    Returns:
        str: Public URL of the uploaded letter
    """
    safe_company = company_name.replace(' ', '_').replace('/', '_')
    filename = f"surat_{mahasiswa_nim}_{safe_company}{os.path.splitext(file.name)[1]}"
    return upload_file_to_firebase(file, folder='surat_penerimaan', filename=filename)


def upload_laporan(file, mahasiswa_nim, laporan_type='kemajuan'):
    """
    Upload report file to Firebase Storage

    Args:
        file: Django UploadedFile object
        mahasiswa_nim: Student NIM
        laporan_type: Type of report ('kemajuan' or 'akhir')

    Returns:
        str: Public URL of the uploaded report
    """
    timestamp = uuid.uuid4().hex[:8]
    filename = f"laporan_{laporan_type}_{mahasiswa_nim}_{timestamp}{os.path.splitext(file.name)[1]}"
    return upload_file_to_firebase(file, folder='laporan', filename=filename)


def upload_company_logo(file, company_name):
    """
    Upload company logo to Firebase Storage

    Args:
        file: Django UploadedFile object
        company_name: Company name

    Returns:
        str: Public URL of the uploaded logo
    """
    safe_company = company_name.replace(' ', '_').replace('/', '_')
    filename = f"logo_{safe_company}{os.path.splitext(file.name)[1]}"
    return upload_file_to_firebase(file, folder='company_logos', filename=filename)


def delete_file_from_firebase(file_url):
    """
    Delete a file from Firebase Storage using its public URL

    Args:
        file_url: Public URL of the file to delete

    Returns:
        bool: True if deletion successful, False otherwise
    """
    try:
        initialize_firebase()

        bucket = storage.bucket()

        blob_path = file_url.split(f'{bucket.name}/')[-1].split('?')[0]

        blob = bucket.blob(blob_path)
        blob.delete()

        return True

    except Exception as e:
        print(f"Error deleting file from Firebase: {str(e)}")
        return False


def get_signed_url(file_url, expiration_hours=24):
    """
    Generate a signed URL for private file access

    Args:
        file_url: Public URL of the file
        expiration_hours: Number of hours until URL expires (default: 24)

    Returns:
        str: Signed URL with expiration
    """
    try:
        initialize_firebase()

        bucket = storage.bucket()

        blob_path = file_url.split(f'{bucket.name}/')[-1].split('?')[0]

        blob = bucket.blob(blob_path)

        url = blob.generate_signed_url(
            version='v4',
            expiration=timedelta(hours=expiration_hours),
            method='GET'
        )

        return url

    except Exception as e:
        print(f"Error generating signed URL: {str(e)}")
        return file_url


def get_file_metadata(file_url):
    """
    Get metadata of a file in Firebase Storage

    Args:
        file_url: Public URL of the file

    Returns:
        dict: File metadata including size, content type, created time
    """
    try:
        initialize_firebase()

        bucket = storage.bucket()

        blob_path = file_url.split(f'{bucket.name}/')[-1].split('?')[0]

        blob = bucket.blob(blob_path)
        blob.reload()

        return {
            'name': blob.name,
            'size': blob.size,
            'content_type': blob.content_type,
            'created': blob.time_created,
            'updated': blob.updated,
            'public_url': blob.public_url
        }

    except Exception as e:
        print(f"Error getting file metadata: {str(e)}")
        return None
