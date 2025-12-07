# COOP STEM - Sistem Cooperative Education 🎓

Sistem manajemen program Cooperative Education untuk STEM Universitas Prasetiya Mulya.

## 🎨 Brand Colors

- **Primary**: #002D72 (Pantone 288 C - Deep Blue)
- **Secondary**: #0066CC (Lighter Blue)
- **Success**: #28A745
- **Warning**: #FFC107
- **Danger**: #DC3545

## ✨ Features

- 📝 Pendaftaran Program Coop dengan upload dokumen
- 💼 Job Posting dan Aplikasi Lowongan
- ✅ Konfirmasi Magang dengan validasi
- 📊 Dashboard untuk Mahasiswa, Supervisor, dan Admin
- 📈 Laporan Kemajuan Bulanan
- 📄 Laporan Akhir
- ⭐ Evaluasi Supervisor (UTS & UAS)
- ⏰ Evaluation Period Control System
- 🏆 Generate Sertifikat Digital dengan QR Code
- 📧 Email Notification System (Microsoft Outlook)
- 🔔 In-App Notifications
- 📁 Firebase Storage untuk File Management
- 🗄️ Supabase PostgreSQL Database

## 🚀 Technology Stack

- **Backend**: Django 5.0+
- **Database**: Supabase PostgreSQL
- **File Storage**: Firebase Storage
- **Email**: Microsoft Outlook SMTP
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Authentication**: Django Auth System

## 📋 Prerequisites

- Python 3.13+
- PostgreSQL (via Supabase)
- Firebase Account
- Microsoft Outlook Account
- Git

## 🛠️ Installation

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd project/coop
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Supabase Database Configuration
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_supabase_password
DB_HOST=db.0ec90b57d6e95fcbda19832f.supabase.co
DB_PORT=5432

# Firebase Configuration
FIREBASE_API_KEY=AIzaSyBXZAAmVddpoZziJaB86ZISmkG6M3K7YKI
FIREBASE_AUTH_DOMAIN=coop-stem.firebaseapp.com
FIREBASE_PROJECT_ID=coop-stem
FIREBASE_STORAGE_BUCKET=coop-stem.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=254673687986
FIREBASE_APP_ID=1:254673687986:web:8fadd6c707201a7718c0ab
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key_with_newlines
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@coop-stem.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk@coop-stem.iam.gserviceaccount.com

# Email Configuration (Microsoft Outlook)
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@outlook.com
EMAIL_HOST_PASSWORD=your_outlook_password
DEFAULT_FROM_EMAIL=your_email@outlook.com
KAPRODI_EMAIL=kaprodi@prasetiyamulya.ac.id
MENTOR_EMAIL=mentor@prasetiyamulya.ac.id
```

## 🔥 Firebase Setup

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project or use existing `coop-stem`
3. Enable Firebase Storage

### 2. Get Service Account Credentials

1. Go to Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Download the JSON file
4. Extract the following values to `.env`:
   - `private_key_id`
   - `private_key` (keep the `\n` characters)
   - `client_email`
   - `client_id`
   - `client_x509_cert_url`

### 3. Configure Storage Security Rules

In Firebase Console → Storage → Rules:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
  }
}
```

## 🗄️ Supabase Setup

### 1. Create Supabase Project

1. Go to [Supabase](https://supabase.com/)
2. Create new project or use existing
3. Get database credentials from Project Settings → Database

### 2. Update .env with Database Credentials

```env
DB_PASSWORD=your_supabase_password
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

## 📧 Microsoft Outlook Email Setup

### 1. Enable SMTP in Outlook

1. Use your Outlook/Microsoft 365 email
2. Enable 2FA if not already enabled
3. Generate App Password:
   - Go to Microsoft Account Security
   - Select "App Passwords"
   - Generate new password for "Mail"

### 2. Update .env with Email Credentials

```env
EMAIL_HOST_USER=your_email@outlook.com
EMAIL_HOST_PASSWORD=generated_app_password
```

## 🏃 Running the Application

### Development Server

```bash
python manage.py runserver
```

Access the application at `http://localhost:8000`

### Default Roles

- **Mahasiswa**: Can register, apply for jobs, submit reports
- **Supervisor**: Can evaluate students, view reports
- **Admin**: Full access to manage system

## 📁 Project Structure

```
coop/
├── accounts/           # User management & authentication
│   ├── models.py      # User, Mahasiswa models
│   ├── views.py       # Login, registration views
│   └── templates/     # Login, register templates
├── coops/             # Core coop functionality
│   ├── models.py      # KonfirmasiMagang, Laporan, Evaluasi, Notification
│   ├── views.py       # Dashboard, reports, certificates
│   ├── static/        # CSS files (brand.css, mahasiswa.css, etc.)
│   └── templates/     # Dashboard templates
├── jobs/              # Job posting system
│   ├── models.py      # JobPosting, JobApplication, Supervisor
│   ├── views.py       # Job listing, applications
│   └── templates/     # Job templates
├── coop/              # Project settings
│   ├── settings.py    # Django configuration
│   ├── firebase/      # Firebase configuration
│   │   └── config.py  # Firebase Storage helpers
│   └── urls.py        # URL routing
└── manage.py          # Django management script
```

## 🎯 Key Features Implementation

### File Upload with Firebase

```python
from coop.firebase.config import FirebaseStorage

# Upload file
file_url = FirebaseStorage.upload_file(
    file=uploaded_file,
    folder=FirebaseStorage.FOLDER_CV,
    filename='optional_custom_name.pdf'
)

# Delete file
FirebaseStorage.delete_file(file_url)
```

### Send Email Notification

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    subject='Your Subject',
    message='Your message',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['recipient@email.com'],
    fail_silently=False,
)
```

### Create Notification

```python
from coops.models import Notification

Notification.objects.create(
    user=user,
    title='Notification Title',
    message='Notification message',
    notification_type='info',  # info, warning, success, danger
    link='/dashboard/'  # Optional link
)
```

## 🎨 Using Brand Colors in Templates

Include the brand CSS in your template:

```html
{% load static %}
<link rel="stylesheet" href="{% static 'brand.css' %}">

<!-- Use brand colors -->
<button class="btn btn-primary">Primary Button</button>
<div class="badge badge-primary">Status</div>
<div class="alert alert-primary">Alert Message</div>
```

## 📊 Database Models

### Key Models

- **User**: Extended Django user with roles (mahasiswa, supervisor, admin)
- **Mahasiswa**: Student profile with document URLs
- **KonfirmasiMagang**: Internship confirmation
- **LaporanKemajuan**: Monthly progress reports
- **LaporanAkhir**: Final report
- **EvaluasiTemplate**: Evaluation templates (UTS/UAS)
- **EvaluasiSupervisor**: Supervisor evaluations
- **SertifikatCoop**: Digital certificates
- **JobPosting**: Job/internship postings
- **JobApplication**: Job applications
- **Notification**: In-app notifications

## 🔐 Security Considerations

- All file uploads go through Firebase Storage
- Database uses Supabase PostgreSQL with secure connection
- Email credentials stored in environment variables
- CSRF protection enabled
- Password validation enforced
- Session timeout configured

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test coops
python manage.py test jobs
```

## 📝 Common Tasks

### Create Admin User

```bash
python manage.py createsuperuser
```

### Make Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collect Static Files

```bash
python manage.py collectstatic
```

### Access Admin Panel

Navigate to `http://localhost:8000/admin/`

## 🐛 Troubleshooting

### Firebase Connection Issues

- Check if service account credentials are correct
- Verify Firebase project ID matches
- Ensure Storage is enabled in Firebase Console

### Email Not Sending

- Verify Outlook app password is correct
- Check if 2FA is enabled on Microsoft account
- Test SMTP connection manually

### Database Connection Issues

- Verify Supabase credentials in .env
- Check if database is accessible
- Ensure psycopg2-binary is installed

## 📚 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [Supabase Documentation](https://supabase.com/docs)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.0/)

## 📄 License

This project is proprietary to STEM Universitas Prasetiya Mulya.

## 👥 Contact

For support or questions, contact:
- Email: stem@prasetiyamulya.ac.id
- Website: https://stem.prasetiyamulya.ac.id/

---

Made with ❤️ by STEM Universitas Prasetiya Mulya
