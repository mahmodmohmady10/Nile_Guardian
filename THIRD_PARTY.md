# التراخيص الخارجية

تعتمد اللعبة على المكونات التالية. كل مكون يبقى تحت ترخيصه الأصلي.

| المكون | الغرض | الترخيص | الرابط |
|---|---|---|---|
| pygame-ce | المحرك الرسومي والصوتي | LGPL-2.1 | https://github.com/pygame-community/pygame-ce |
| arabic-reshaper | تشكيل الحروف العربية (مسار احتياطي) | MIT | https://github.com/mpcabd/python-arabic-reshaper |
| python-bidi | اتجاه النص RTL (مسار احتياطي) | LGPL | https://github.com/MeirKriheli/python-bidi |
| pytest, pytest-cov, ruff | الاختبارات وفحص الأسلوب (للمطورين فقط، لا تُوزَّع) | MIT | — |
| PyInstaller | تغليف الملف التنفيذي (للبناء فقط) | GPL مع استثناء للملفات الناتجة | https://pyinstaller.org |
| Tajawal (خط عربي) | خط النصوص | SIL Open Font License 1.1 | https://fonts.google.com/specimen/Tajawal |

## ملاحظات
- ملف الخط `Tajawal-Regular.ttf` يجب أن يُرفق معه نص ترخيص OFL في `assets/fonts/OFL.txt` عند التوزيع.
- الأصوات والموسيقى (عند إضافتها) سيُذكر مصدرها وترخيصها هنا.
- أي مكون جديد يُضاف يجب أن يُسجَّل في هذا الملف.
