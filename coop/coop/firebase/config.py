"""
Firebase Configuration for COOP-STEM
Handles Firebase initialization and storage operations
"""
import firebase_admin
from firebase_admin import credentials, storage
from django.conf import settings
import os
import uuid
from datetime import timedelta

# Initialize Firebase
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Firebase config from settings
        firebase_config = {
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
            "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n') if hasattr(settings, 'FIREBASE_PRIVATE_KEY') else None,
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "client_id": settings.FIREBASE_CLIENT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": settings.FIREBASE_CERT_URL if hasattr(settings, 'FIREBASE_CERT_URL') else ""
        }

        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {
            'storageBucket': settings.FIREBASE_STORAGE_BUCKET
        })

def get_storage_bucket():
    """Get Firebase storage bucket"""
    initialize_firebase()
    return storage.bucket()


class FirebaseStorage:
    """Helper class for Firebase Storage operations"""

    FOLDER_CV = 'cv'
    FOLDER_PORTFOLIO = 'portfolio'
    FOLDER_SPTJM = 'sptjm'
    FOLDER_KONSULTASI = 'konsultasi'
    FOLDER_SURAT_MAGANG = 'surat_magang'
    FOLDER_LAPORAN = 'laporan'
    FOLDER_SERTIFIKAT = 'sertifikat'
    FOLDER_COMPANY_LOGOS = 'company_logos'

    @staticmethod
    def upload_file(file, folder, filename=None):
        """
        Upload file to Firebase Storage

        Args:
            file: Django UploadedFile object
            folder: Folder name in Firebase Storage
            filename: Optional custom filename (will generate UUID if not provided)

        Returns:
            Public URL of uploaded file
        """
        try:
            bucket = get_storage_bucket()

            # Generate secure filename
            if not filename:
                ext = os.path.splitext(file.name)[1]
                filename = f"{uuid.uuid4()}{ext}"

            # Create blob path
            blob_path = f"{folder}/{filename}"
            blob = bucket.blob(blob_path)

            # Upload file
            blob.upload_from_file(file, content_type=file.content_type)

            # Make publicly accessible
            blob.make_public()

            return blob.public_url

        except Exception as e:
            print(f"Error uploading file to Firebase: {str(e)}")
            raise e

    @staticmethod
    def delete_file(file_url):
        """
        Delete file from Firebase Storage

        Args:
            file_url: Public URL of the file to delete

        Returns:
            Boolean indicating success
        """
        try:
            bucket = get_storage_bucket()

            # Extract blob path from URL
            # URL format: https://storage.googleapis.com/bucket-name/path/to/file
            blob_path = file_url.split(f"{settings.FIREBASE_STORAGE_BUCKET}/")[-1].split("?")[0]

            blob = bucket.blob(blob_path)
            blob.delete()

            return True

        except Exception as e:
            print(f"Error deleting file from Firebase: {str(e)}")
            return False

    @staticmethod
    def get_signed_url(file_url, expiration_minutes=60):
        """
        Generate signed URL for private file access

        Args:
            file_url: Public URL of the file
            expiration_minutes: URL expiration time in minutes

        Returns:
            Signed URL string
        """
        try:
            bucket = get_storage_bucket()

            # Extract blob path from URL
            blob_path = file_url.split(f"{settings.FIREBASE_STORAGE_BUCKET}/")[-1].split("?")[0]

            blob = bucket.blob(blob_path)

            # Generate signed URL
            url = blob.generate_signed_url(
                expiration=timedelta(minutes=expiration_minutes),
                method='GET'
            )

            return url

        except Exception as e:
            print(f"Error generating signed URL: {str(e)}")
            return file_url

    @staticmethod
    def file_exists(file_url):
        """
        Check if file exists in Firebase Storage

        Args:
            file_url: Public URL of the file

        Returns:
            Boolean indicating if file exists
        """
        try:
            bucket = get_storage_bucket()

            blob_path = file_url.split(f"{settings.FIREBASE_STORAGE_BUCKET}/")[-1].split("?")[0]
            blob = bucket.blob(blob_path)

            return blob.exists()

        except Exception as e:
            print(f"Error checking file existence: {str(e)}")
            return False
