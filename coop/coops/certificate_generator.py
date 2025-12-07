"""
Certificate PDF Generator with QR Code
Generates professional certificates for Coop program completion
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER
import qrcode
from PIL import Image
from django.conf import settings


class CertificateGenerator:
    """Generate professional certificate PDFs with QR code"""

    def __init__(self, sertifikat):
        self.sertifikat = sertifikat
        self.konfirmasi = sertifikat.konfirmasi
        self.mahasiswa = sertifikat.konfirmasi.mahasiswa
        self.width, self.height = landscape(A4)

    def generate_qr_code(self):
        """Generate QR code for certificate verification"""
        qr_data = f"CERT-{self.sertifikat.nomor_sertifikat}"
        verification_url = f"https://coop.prasetiyamulya.ac.id/verify/{self.sertifikat.nomor_sertifikat}/"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer

    def draw_border(self, c):
        """Draw decorative border"""
        c.setStrokeColor(colors.HexColor(settings.BRAND_PRIMARY_COLOR))
        c.setLineWidth(3)

        margin = 0.5 * inch
        c.rect(margin, margin, self.width - 2 * margin, self.height - 2 * margin)

        c.setStrokeColor(colors.HexColor(settings.BRAND_SECONDARY_COLOR))
        c.setLineWidth(1)
        inner_margin = margin + 0.1 * inch
        c.rect(inner_margin, inner_margin,
               self.width - 2 * inner_margin,
               self.height - 2 * inner_margin)

    def generate_pdf(self):
        """Generate the complete certificate PDF"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape(A4))

        self.draw_border(c)

        c.setFont("Helvetica-Bold", 32)
        c.setFillColor(colors.HexColor(settings.BRAND_PRIMARY_COLOR))
        c.drawCentredString(self.width / 2, self.height - 1.5 * inch, "SERTIFIKAT")

        c.setFont("Helvetica", 16)
        c.setFillColor(colors.black)
        c.drawCentredString(self.width / 2, self.height - 1.9 * inch,
                           "COOPERATIVE EDUCATION PROGRAM")

        c.setFont("Helvetica", 12)
        c.drawCentredString(self.width / 2, self.height - 2.3 * inch,
                           "Diberikan kepada:")

        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(colors.HexColor(settings.BRAND_PRIMARY_COLOR))
        c.drawCentredString(self.width / 2, self.height - 2.9 * inch,
                           self.mahasiswa.get_full_name())

        c.setFont("Helvetica", 12)
        c.setFillColor(colors.black)

        try:
            mahasiswa_obj = self.mahasiswa.mahasiswa
            nim_text = f"NIM: {mahasiswa_obj.nim}"
            prodi_text = f"{mahasiswa_obj.prodi}"
        except:
            nim_text = f"Username: {self.mahasiswa.username}"
            prodi_text = "Universitas Prasetiya Mulya"

        c.drawCentredString(self.width / 2, self.height - 3.3 * inch, nim_text)
        c.drawCentredString(self.width / 2, self.height - 3.6 * inch, prodi_text)

        c.setFont("Helvetica", 11)
        text_y = self.height - 4.2 * inch
        c.drawCentredString(self.width / 2, text_y,
                           f"Telah menyelesaikan program Cooperative Education (Coop)")
        c.drawCentredString(self.width / 2, text_y - 0.3 * inch,
                           f"di {self.konfirmasi.nama_perusahaan}")
        c.drawCentredString(self.width / 2, text_y - 0.6 * inch,
                           f"Periode: {self.konfirmasi.periode_awal.strftime('%d %B %Y')} - "
                           f"{self.konfirmasi.periode_akhir.strftime('%d %B %Y')}")
        c.drawCentredString(self.width / 2, text_y - 0.9 * inch,
                           f"Posisi: {self.konfirmasi.posisi}")

        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor(settings.BRAND_SUCCESS_COLOR))
        c.drawCentredString(self.width / 2, text_y - 1.4 * inch,
                           f"Nilai Akhir: {self.sertifikat.nilai_akhir}")

        qr_buffer = self.generate_qr_code()
        qr_img = Image.open(qr_buffer)

        qr_size = 0.8 * inch
        qr_x = self.width - 1.5 * inch
        qr_y = 0.8 * inch

        c.drawImage(qr_buffer, qr_x, qr_y, width=qr_size, height=qr_size, mask='auto')

        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        c.drawCentredString(qr_x + qr_size / 2, qr_y - 0.2 * inch, "Scan untuk verifikasi")

        c.setFont("Helvetica", 10)
        signature_y = 1.2 * inch
        signature_x_left = self.width / 4
        signature_x_right = 3 * self.width / 4

        c.drawCentredString(signature_x_left, signature_y + 0.7 * inch,
                           self.sertifikat.tanggal_kelulusan.strftime('%d %B %Y'))

        c.line(signature_x_left - 1.2 * inch, signature_y,
               signature_x_left + 1.2 * inch, signature_y)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(signature_x_left, signature_y - 0.2 * inch, "Tanggal")

        c.setFont("Helvetica", 10)
        c.line(signature_x_right - 1.2 * inch, signature_y,
               signature_x_right + 1.2 * inch, signature_y)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(signature_x_right, signature_y - 0.2 * inch,
                           "Koordinator Program Coop")

        c.setFont("Helvetica", 7)
        c.setFillColor(colors.grey)
        c.drawCentredString(self.width / 2, 0.4 * inch,
                           f"Nomor Sertifikat: {self.sertifikat.nomor_sertifikat}")
        c.drawCentredString(self.width / 2, 0.25 * inch,
                           "STEM - Universitas Prasetiya Mulya")

        c.showPage()
        c.save()

        buffer.seek(0)
        return buffer
