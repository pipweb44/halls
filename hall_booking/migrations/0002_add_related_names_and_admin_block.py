# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hall_booking', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='is_admin_block',
            field=models.BooleanField(default=False, verbose_name='حجب إداري'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='hall',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='bookings', to='hall_booking.hall', verbose_name='القاعة'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='user_bookings', to='auth.user', verbose_name='المستخدم'),
        ),
    ]
