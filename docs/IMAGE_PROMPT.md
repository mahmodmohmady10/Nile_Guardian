# وصف إنشاء صورة الحيوانات

## الهدف
صورة واحدة تحتوي على الحيوانات الستة في شبكة 3×2، ثم تُقطّع إلى صور فردية بالسكربت `tools/slice_sheet.py`.

## الوصف (للنسخ إلى أداة توليد الصور)

```
Game sprite sheet of six African wildlife animals from Sudan, in a painted semi-realistic
2D game art style with clean dark outlines and soft shading. All animals face right, in a
side view, full body visible. Arranged in a 3 by 2 grid, each animal centered in its own
equal cell with generous empty space around it, consistent scale and lighting, identical
art style for all six. Top row from left to right: a golden-brown falcon with folded wings
and a yellow beak, a tan reem gazelle with curved horns, a green Nile crocodile resting at
the water's edge. Bottom row from left to right: a grey wolf, a spotted yellow leopard, a
male lion with a dark mane. Plain solid bright green background (#00FF00), flat and even,
no shadows on the background, no ground, no scenery. No text, no labels, no borders, no
watermark, no extra animals or objects.
```

## الوصف السلبي (إن وُجد حقل منفصل)
```
text, letters, labels, border, frame, watermark, signature, background scenery, ground,
shadow on background, multiple copies, cropped animals, blurry, low detail, deformed
```

## المواصفات
- **الحجم:** 1536 × 1024 بكسل (كل خانة 512 × 512)، أو أي حجم بنسبة 3:2.
- **الخلفية:** أخضر صافٍ #00FF00، ليحذفه السكربت تلقائياً.
- **الصيغة:** PNG.
- **الترتيب:** صقر الجديان، غزال الريم، تمساح النيل (الصف الأول)، ثم الذئب، النمر، أسد الدندر (الصف الثاني).

## إن لم تنجح الصورة الواحدة
أنشئ كل حيوان بصورة منفصلة بالوصف نفسه، مع تغيير الجزء الخاص بالحيوان فقط، وضع كل صورة بخلفية خضراء بالحجم نفسه. ثم ضعها في شبكة 3×2 بأي برنامج تحرير قبل التقطيع.

## التقطيع
من جذر المشروع، بعد تفعيل البيئة:
```bat
python tools/slice_sheet.py C:\path\to\sheet.png
```
الناتج: ستة ملفات في `data/images/animals/` بخلفية شفافة وحجم 128×128.

## ملاحظات قانونية
الصور المولّدة بالذكاء الاصطناعي تخضع لشروط الأداة التي استخدمتها. أضف ذكر الأداة في `THIRD_PARTY.md` عند النشر.
