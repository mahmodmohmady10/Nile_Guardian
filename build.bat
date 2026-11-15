@echo off
REM بناء NileGuardian.exe من جذر المشروع. شغّل هذا الملف بعد تفعيل البيئة الافتراضية.
REM قبل البناء: ضع Tajawal-Regular.ttf في assets\fonts\

if not exist "assets\fonts\Tajawal-Regular.ttf" (
    echo تحذير: الخط العربي غير موجود في assets\fonts\ ، لن تعمل النصوص العربية في الملف الناتج.
)

python -m pip install --upgrade pyinstaller
if errorlevel 1 goto :fail

python -m PyInstaller --noconfirm nile_guardian.spec
if errorlevel 1 goto :fail

echo.
echo اكتمل البناء: dist\NileGuardian.exe
exit /b 0

:fail
echo فشل البناء. أرسل نص الخطأ كاملاً للمراجعة.
exit /b 1
