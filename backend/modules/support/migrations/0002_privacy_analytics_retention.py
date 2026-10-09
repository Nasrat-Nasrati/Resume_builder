from django.db import migrations


def add_retention_notice(apps, schema_editor):
    Content = apps.get_model("support", "PublicContent")
    Content.objects.get_or_create(
        key="privacy",
        version="draft-2",
        defaults={
            "status": "draft",
            "title_by_language": {
                "en": "Privacy notice — draft",
                "fa": "اطلاعیهٔ حریم خصوصی — پیش‌نویس",
                "ps": "د محرمیت خبرتیا — مسوده",
            },
            "body_by_language": {
                "en": [
                    "This draft describes the current application foundation and requires review before publication.",
                    "The service stores account details, CV content, profile photos, private export files and support requests when you use those features. Passwords are stored using Django's password hashing. CV files are served only through authenticated owner-scoped routes.",
                    "No payment provider is currently integrated and no payment credentials are collected by the browser. Optional aggregate page-view measurement is sent only after analytics consent; it stores a page path and Kabul-local date, not visitor identifiers, and raw daily aggregates are pruned after 90 days. Production hosting, email provider, backup schedule and contact-data deletion process remain undecided.",
                    "This notice does not promise end-to-end encryption or zero sharing. The final processors, retention schedule, account deletion process and applicable rights need approval before publication.",
                ],
                "fa": [
                    "این مسوده وضعیت فعلی زیربنای برنامه را توضیح می‌دهد و پیش از انتشار به بازبینی نیاز دارد.",
                    "هنگام استفاده از خدمات، اطلاعات حساب، محتوای سی‌وی، عکس پروفایل، فایل‌های خروجی خصوصی و درخواست‌های پشتیبانی ذخیره می‌شود. رمزها با هش‌گذاری Django ذخیره می‌شوند و فایل‌های سی‌وی فقط از مسیرهای مجاز مالک ارائه می‌شوند.",
                    "فراهم‌کنندهٔ پرداخت وصل نشده و مرورگر اطلاعات پرداخت نمی‌گیرد. سنجش اختیاری بازدید صفحات فقط پس از رضایت تحلیل انجام می‌شود؛ مسیر صفحه و تاریخ کابل ذخیره می‌شود، شناسهٔ بازدیدکننده ذخیره نمی‌شود و دادهٔ خام روزانه پس از ۹۰ روز حذف می‌شود. میزبانی تولید، ایمیل، پشتیبان‌گیری و روند حذف اطلاعات تماس هنوز تعیین نشده است.",
                    "این اطلاعیه رمزنگاری سرتاسری یا عدم اشتراک‌گذاری مطلق را وعده نمی‌دهد. پردازشگران، مدت نگهداری، حذف حساب و حقوق مربوطه باید پیش از انتشار تأیید شوند.",
                ],
                "ps": [
                    "دا مسوده د اپ د اوسني بنسټ حالت بیانوي او د خپرېدو مخکې بیاکتنې ته اړتیا لري.",
                    "د خدمتونو د کارولو پر مهال د حساب معلومات، د سي وي منځپانګه، انځورونه، شخصي صادر شوي فایلونه او د ملاتړ غوښتنې ساتل کېږي. پاسورډونه د Django په هش کولو ساتل کېږي او سي وي فایلونه یوازې د مالک له اجازې لرونکو لارو وړاندې کېږي.",
                    "د پیسو برابرونکی نه دی نښلول شوی او براوزر د پیسو معلومات نه اخلي. اختیاري د پاڼې کتنې یوازې د تحلیل له اجازې وروسته لېږل کېږي؛ د پاڼې لاره او د کابل نېټه ساتل کېږي، د لیدونکي پېژندنه نه ساتل کېږي او ورځني خام شمېرې تر ۹۰ ورځو وروسته ړنګېږي. د تولید کوربه، برېښنالیک، شاتړونه او د اړیکو د معلوماتو د ړنګولو کړنلاره لا نه ده ټاکل شوې.",
                    "دا خبرتیا د پای-تر-پایه کوډولو یا د هېڅ شریکولو مطلق ضمانت نه ورکوي. پروسس کوونکي، د ساتلو موده، د حساب ړنګول او اړوند حقونه باید د خپرېدو مخکې تایید شي.",
                ],
            },
        },
    )


class Migration(migrations.Migration):
    dependencies = [("support", "0001_initial")]
    operations = [migrations.RunPython(add_retention_notice, migrations.RunPython.noop)]
