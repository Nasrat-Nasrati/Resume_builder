from django.db import migrations, models
import django.db.models.deletion
import uuid


def seed_public_content(apps, schema_editor):
    Content = apps.get_model("support", "PublicContent")
    Content.objects.get_or_create(key="faq", version="1", defaults={
        "status": "published",
        "title_by_language": {"en": "Frequently asked questions", "fa": "پرسش‌های رایج", "ps": "ډېرې پوښتل شوې پوښتنې"},
        "body_by_language": {
            "en": ["Free accounts can export up to five distinct CVs in a rolling 24-hour window. A CV counts only after its first successful export; previews and re-downloads do not use another credit.", "Premium is configured for twenty exports in a rolling 24-hour window, PDF and Word exports, and premium templates. Premium purchases are currently unavailable while merchant and provider setup is pending.", "The builder supports English, Dari and Pashto output. Your authored text is not automatically translated.", "An ATS-oriented layout uses plain text and a single column, but no layout can guarantee acceptance by every employer's applicant tracking system."],
            "fa": ["حساب رایگان می‌تواند در هر بازهٔ چرخان ۲۴ ساعته حداکثر پنج سی‌وی متمایز را صادر کند. هر سی‌وی فقط پس از نخستین صدور موفق محاسبه می‌شود؛ پیش‌نمایش و بارگیری دوباره اعتبار دیگری مصرف نمی‌کند.", "طرح پریمیوم برای بیست صدور در بازهٔ چرخان ۲۴ ساعته، صدور PDF و Word و قالب‌های پریمیوم پیکربندی شده است. خرید پریمیوم تا تکمیل تأیید فروشنده و فراهم‌کننده در دسترس نیست.", "خروجی سازنده به انگلیسی، دری و پشتو پشتیبانی می‌شود. متن شما به‌طور خودکار ترجمه نمی‌شود.", "قالب مناسب ATS از متن ساده و یک ستون استفاده می‌کند؛ هیچ قالبی پذیرش در همهٔ سیستم‌های استخدام را تضمین نمی‌کند."],
            "ps": ["وړیا حساب په هر ګرځنده ۲۴ ساعتونو کې تر پنځو بېلابېلو سي وي ګانو صادرولی شي. سي وي یوازې د لومړي بریالي صادرېدو وروسته شمېرل کېږي؛ مخکتنه او بیا ښکته کول بله کریډیټ نه کاروي.", "پریمیم پلان په ګرځنده ۲۴ ساعتونو کې د شلو صادرونو، PDF او Word او پریمیم قالبونو لپاره برابر شوی. د سوداګر او برابرونکي د چمتووالي تر بشپړېدو پریمیم پېرود نشته.", "د سي وي د وتلو ژبې انګلیسي، دري او پښتو دي. ستاسو لیکل شوی متن په اتومات ډول نه ژباړل کېږي.", "د ATS لپاره قالب ساده متن او یوه ستنه کاروي؛ هېڅ قالب د ټولو استخدامي سیسټمونو د منلو ضمانت نه شي کولای."]
        }})
    Content.objects.get_or_create(key="privacy", version="draft-1", defaults={
        "status": "draft", "title_by_language": {"en": "Privacy notice — draft", "fa": "اطلاعیهٔ حریم خصوصی — پیش‌نویس", "ps": "د محرمیت خبرتیا — مسوده"},
        "body_by_language": {"en": ["This draft describes the current application foundation and requires review before publication.", "The service stores account details, CV content, profile photos, private export files and support requests when you use those features. Passwords are stored using Django's password hashing. CV files are served only through authenticated owner-scoped routes.", "No payment provider is currently integrated and no payment credentials are collected by the browser. Optional aggregate page-view measurement is sent only after analytics consent; it stores a page path and Kabul-local date, not visitor identifiers, and raw daily aggregates are pruned after 90 days. The production hosting, email provider, backup schedule and contact-data deletion process have not yet been selected.", "This notice does not promise end-to-end encryption or zero sharing. The final processors, retention schedule, account deletion process and applicable rights need approval before publication."],
            "fa": ["این پیش‌نویس وضعیت فعلی برنامه را توصیف می‌کند و پیش از انتشار به بازبینی نیاز دارد.", "در صورت استفاده از امکانات، اطلاعات حساب، محتوای سی‌وی، عکس پروفایل، فایل‌های خصوصی و درخواست‌های پشتیبانی ذخیره می‌شوند. رمزها با سازوکار هش Django نگهداری می‌شوند و فایل‌های سی‌وی فقط از مسیرهای مجاز مالک در دسترس‌اند.", "هنوز فراهم‌کنندهٔ پرداختی وصل نشده و مرورگر اطلاعات پرداخت نمی‌گیرد. میزبان تولید، فراهم‌کنندهٔ ایمیل، پشتیبان‌گیری، مدت نگهداری و روند حذف اطلاعات پشتیبانی هنوز تعیین نشده است.", "این اطلاعیه رمزنگاری سرتاسری یا عدم اشتراک‌گذاری مطلق را وعده نمی‌دهد. پردازشگران، مدت نگهداری، روند حذف حساب و حقوق مربوطه باید پیش از انتشار تأیید شوند."],
            "ps": ["دا مسوده د اوسني اپ بنسټیز حالت بیانوي او د خپرېدو مخکې بیاکتنې ته اړتیا لري.", "د ځانګړنو د کارولو پر مهال د حساب معلومات، د سي وي منځپانګه، د پروفایل انځورونه، شخصي صادر شوي فایلونه او د ملاتړ غوښتنې ساتل کېږي. پاسورډونه د Django د هش کولو په وسیله زېرمه کېږي او سي وي فایلونه یوازې د مالک له اجازې لرونکو لارو وړاندې کېږي.", "د پیسو برابرونکی نه دی نښلول شوی او براوزر د پیسو معلومات نه اخلي. اختیاري د پاڼې کتنې یوازې د تحلیل له اجازې وروسته لېږل کېږي؛ د پاڼې لاره او د کابل نېټه ساتل کېږي، د لیدونکي پېژندنه نه ساتل کېږي، او ورځني خام شمېرې تر ۹۰ ورځو وروسته ړنګېږي. د تولید کوربه، برېښنالیک برابرونکی، شاتړونه او د ملاتړ معلوماتو د ړنګولو کړنلاره لا نه ده ټاکل شوې.", "دا خبرتیا د پای-تر-پایه کوډولو یا د هېڅ شریکولو مطلق ضمانت نه ورکوي. د خپرېدو مخکې باید پروسس کوونکي، د ساتلو موده، د حساب ړنګول او اړوند حقونه تایید شي."]}})
    Content.objects.get_or_create(key="terms", version="draft-1", defaults={
        "status": "draft", "title_by_language": {"en": "Terms — draft", "fa": "شرایط استفاده — پیش‌نویس", "ps": "د کارونې شرایط — مسوده"},
        "body_by_language": {"en": ["This draft requires review before publication. KabulCV currently provides a resume builder and private PDF previews and exports.", "The Free plan currently allows five distinct CVs per rolling 24 hours. Premium capabilities are configured but purchases are disabled, and no Premium price has been approved.", "The rules for refunds, cancellations, complaints, account retention, governing law and service availability have not been confirmed. This draft is not a final legal agreement."],
            "fa": ["این پیش‌نویس پیش از انتشار به بازبینی نیاز دارد. KabulCV در حال حاضر سازندهٔ سی‌وی و پیش‌نمایش و صدور خصوصی PDF ارائه می‌کند.", "طرح رایگان فعلی اجازهٔ صدور پنج سی‌وی متمایز در بازهٔ چرخان ۲۴ ساعته را می‌دهد. قابلیت‌های پریمیوم پیکربندی شده‌اند، اما خرید غیرفعال است و قیمت تأیید نشده است.", "قواعد بازپرداخت، لغو، شکایت، نگهداری حساب، قانون حاکم و دسترس‌پذیری سرویس تأیید نشده‌اند. این متن توافق نهایی حقوقی نیست."],
            "ps": ["دا مسوده د خپرېدو مخکې بیاکتنې ته اړتیا لري. KabulCV اوس د سي وي جوړولو، شخصي PDF مخکتنې او صادرولو خدمت برابروي.", "وړیا پلان په هر ګرځنده ۲۴ ساعتونو کې د پنځو بېلابېلو سي وي ګانو د صادرولو اجازه لري. د پریمیم وړتیاوې برابرې دي خو پېرود بند دی او بیه نه ده تایید شوې.", "د بېرته ورکولو، لغوه کولو، شکایتونو، حساب ساتلو، حاکم قانون او خدمت شتون اصول نه دي منل شوي. دا وروستی حقوقي تړون نه دی."]}
    })


def unseed_public_content(apps, schema_editor):
    apps.get_model("support", "PublicContent").objects.all().delete()


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name="ContactSubmission", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("sender_email", models.EmailField(max_length=254)),
            ("category", models.CharField(max_length=24)),
            ("subject", models.CharField(max_length=160)),
            ("message", models.TextField(max_length=5000)),
            ("delivery_status", models.CharField(choices=[("queued", "Queued"), ("sent", "Sent"), ("unavailable", "Unavailable"), ("failed", "Failed")], default="queued", max_length=16)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name="PublicContent", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("key", models.SlugField(max_length=24)),
            ("version", models.CharField(max_length=40)),
            ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], default="draft", max_length=12)),
            ("title_by_language", models.JSONField(default=dict)),
            ("body_by_language", models.JSONField(default=dict)),
            ("updated_at", models.DateTimeField(auto_now=True)),
        ], options={"ordering": ["key", "-updated_at"], "constraints": [models.UniqueConstraint(fields=("key", "version"), name="unique_public_content_version")]}),
        migrations.RunPython(seed_public_content, unseed_public_content),
    ]
