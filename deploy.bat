@echo off
REM نشر النموذج بأمر واحد: توليد البيانات + رفع إلى GitHub (يُعاد بناء الرابط الحيّ تلقائيًّا).
REM الاستخدام:  deploy.bat "وصف التعديل"
chcp 65001 >nul
cd /d "%~dp0"
set "MSG=%~1"
if "%MSG%"=="" set "MSG=update: تطوير النموذج"

echo [1/4] توليد بيانات المشهد...
python build_site.py || (echo   ** فشل توليد النموذج ** & exit /b 1)

echo [2/4] (اختياري) لإخراج لقطات Blender جديدة شغّل يدويًّا:
echo        blender -b --python blender_build.py -- cycles all

echo [3/4] رفع التغييرات إلى GitHub...
git add -A
git commit -m "%MSG%" || echo   (لا تغييرات جديدة للرفع)
git push || (echo   ** فشل الدفع — تحقّق من اتصالك/صلاحياتك ** & exit /b 1)

echo [4/4] تم. يُعاد بناء الرابط الحيّ خلال نحو دقيقة:
echo        https://albarshi996.github.io/GM155/
