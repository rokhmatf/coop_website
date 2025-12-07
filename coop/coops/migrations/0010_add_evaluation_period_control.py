from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coops', '0009_remove_weeklyreport_coops_weeklyreport_student_week_start_date_uniq_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluasitemplate',
            name='periode_mulai',
            field=models.DateTimeField(null=True, blank=True, verbose_name='Periode Mulai', help_text='Tanggal dan waktu mulai periode pengisian evaluasi'),
        ),
        migrations.AddField(
            model_name='evaluasitemplate',
            name='periode_selesai',
            field=models.DateTimeField(null=True, blank=True, verbose_name='Periode Selesai', help_text='Tanggal dan waktu akhir periode pengisian evaluasi'),
        ),
        migrations.AddField(
            model_name='evaluasitemplate',
            name='auto_distribute',
            field=models.BooleanField(default=False, verbose_name='Auto Distribute', help_text='Otomatis distribute evaluasi ke supervisor saat periode dimulai'),
        ),
    ]
