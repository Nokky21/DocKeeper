<div align="center">

# DocKeeper

**توثيق لا يتعفّن.**

يكتب وكيل البرمجة لديك التوثيق. يربط DocKeeper كل ادعاء بالشيفرة التي تقف وراءه، ويخبرك فور تغيّر تلك الشيفرة.

[![CI](https://github.com/Nokky21/DocKeeper/actions/workflows/ci.yml/badge.svg)](https://github.com/Nokky21/DocKeeper/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-2ea44f)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](../../LICENSE)

[الموقع](https://nokky21.github.io/DocKeeper/) · [عرض حي](https://nokky21.github.io/DocKeeper/#demo) · [التثبيت](#install) · [المرجع](../reference.md)

<sub>[English](../../README.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [Türkçe](README.tr.md) · **العربية** · [עברית](README.he.md) · [हिन्दी](README.hi.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md) · [ไทย](README.th.md)</sub>

</div>

---

## لماذا

ملف README المكتوب اليوم يصبح خاطئًا بعد بضعة أشهر، ولا أحد يعرف أي الصفحات تكذب. يحلّ DocKeeper مشكلة «لا أحد يعرف» مجانًا وعلى جهازك:

- **كل ادعاء يُتحقَّق منه.** عبارة «تُتحقَّق المدفوعات قبل تحصيلها» مربوطة بالدالة التي تقوم بذلك. وعندما تتغيّر تلك الدالة، يخبرك DocKeeper.
- **لا ذكاء اصطناعي في التحقق.** وكيلك يكتب، والتحقق يقارن البصمات، لذا يعطي الجواب نفسه في كل مرة.
- **محلي ومجاني.** بلا حساب، بلا خادم، بلا شبكة، بلا تبعيات. ترخيص MIT.

## كيف يعمل

<p align="center"><img src="../../site/public/assets/how-it-works.svg" alt="كيف يعمل DocKeeper: يُربط الادعاء بكتلة شيفرة، وتُحسب بصمة الكتلة، ويُبلغ check بنتيجة OK أو MOVED أو CHANGED" width="100%"></p>

1. **اربط.** بجانب كل ادعاء، يكتب الوكيل مكانه في الشيفرة: `[[src/payments.py#validate_payment]]`، أو الشيء نفسه داخل تعليق HTML لتبقى الصفحة نظيفة.
2. **اختم.** يحسب `dockeeper scan` بصمة الشيفرة خلف كل مرساة، وهي عادةً الدالة كاملة. إعادة التنسيق لا تهم؛ أما تغيير المنطق فيهم.
   <!-- dockeeper: dockeeper/bloques.py#bloque_en dockeeper/huellas.py#huella -->
3. **تحقّق.** يعطي `dockeeper check` حكمًا لكل ادعاء: `OK`؛ أو `MOVED` (انتقلت الشيفرة، ويتبعها `dockeeper fix` دون حاجة إلى مراجعة)؛ أو `CHANGED` (تغيّرت الشيفرة، فيقرأها شخص ويحدّث النص). أي `CHANGED` يجعل الأمر يخرج بالرمز 1، فيفشل CI.
   <!-- dockeeper: dockeeper/motor.py#verificar_codigo dockeeper/motor.py#FALLOS -->

<p align="center"><img src="../../site/public/assets/terminal-check.svg" alt="مخرجات حقيقية لـ dockeeper check بعد تعديل الشيفرة: ادعاء CHANGED وآخر MOVED" width="100%"></p>

<a id="install"></a>

## التثبيت

تحتاج إلى `python3` (الإصدار 3.10 أو أحدث) و`git`. انسخ المستودع إلى مجلد اسمه `dockeeper` بالضبط:

```bash
# Claude Code
git clone https://github.com/Nokky21/DocKeeper.git ~/.claude/skills/dockeeper

# Codex, Gemini CLI, Cursor, GitHub Copilot
git clone https://github.com/Nokky21/DocKeeper.git ~/.agents/skills/dockeeper
```

مجلدات أخرى، مشروع واحد، Windows، claude.ai والواجهة البرمجية: راجع [دليل التثبيت](../install.md).

## الاستخدام

اطلب من وكيلك بكلماتك:

- *«وثّق هذا المستودع باستخدام dockeeper.»* والمستودعات الأحادية أيضًا، حزمةً بعد حزمة.
- *«تحقّق مما إذا كان توثيقنا ما زال صحيحًا وأصلح ما لم يعد كذلك.»*
- *«راجع التوثيق مع كل commit.»* يثبّت خطاف git لا يمنع أي commit أبدًا.
- *«اكتب صفحة القرارات من سجل git. لا تخترع أسبابًا.»*

أو شغّله بنفسك من جذر مشروعك:

```bash
DK="python3 $HOME/.claude/skills/dockeeper/bin/dockeeper"
$DK audit    # ما الناقص: صفحات، حزم، شيفرة غير موثّقة
$DK scan     # يختم المراسي الجديدة ويعرض الشيفرة التي تشير إليها كل واحدة
$DK check    # ما زال صحيحًا؟ الخروج 0 = نعم، 1 = تغيّر شيء ما
$DK fix      # يتبع الشيفرة التي انتقلت (لا يلمس إلا ملف الختم)
$DK review   # ماذا يعني آخر commit للتوثيق
```

<!-- dockeeper: dockeeper/motor.py#arreglar -->

## مع كل commit

ينظر `review` في آخر commit (أو في فرع كامل باستخدام `--desde main`) ويسرد الادعاءات التي مسّها، والشيفرة الجديدة أو المعدّلة التي لا يغطيها أي ادعاء بعد، والقرارات الواردة في تلك الـ commits وغير المكتوبة. وبوصفه خطاف `post-commit`، يرى من يُجري الـ commit، أنت أو وكيلك، هذه القائمة في كل مرة، فينمو التوثيق مع الشيفرة:
<!-- dockeeper: dockeeper/revision.py#revisar -->

```sh
#!/bin/sh
python3 "$HOME/.claude/skills/dockeeper/bin/dockeeper" review || true
```

## المستودعات الأحادية

يعثر `audit` على كل حزمة (أي مجلد فرعي فيه `package.json` أو `go.mod` أو `Cargo.toml` أو `pyproject.toml` أو `pom.xml` وما شابه) ويبيّن أيّها بلا توثيق. يكتب الوكيل صفحات الجذر مع خريطة للحزم، ثم يوثّق حزمةً بعد حزمة، فيتسع الأمر حتى لمستودع ضخم. <!-- dockeeper: dockeeper/paquetes.py#detectar -->

## في CI

```yaml
- uses: actions/checkout@v6
- uses: Nokky21/DocKeeper@v0.1.0
```

أي نظام CI آخر لا يحتاج إلا إلى Python و git: [انسخه وشغّل `check`](../reference.md#continuous-integration).

## للمزيد

- [دليل التثبيت](../install.md): كل الوكلاء، مشروع واحد، Windows، claude.ai والواجهة البرمجية.
- [المرجع](../reference.md): المراسي، الأوامر، الأحكام، النطاق الجزئي، التوثيق المنشور، «لماذا»، الإعداد، الحدود والأسئلة الشائعة.
- [SKILL.md](../../SKILL.md)، التعليمات التي يتبعها وكيلك، و[المواصفة](../../SPEC.md) (كلاهما بالإسبانية).

## الترخيص

[MIT](../../LICENSE).

---

<sub>ترجمة لـ [ملف README الإنجليزي](../../README.md)، وهو المرجع عند الاختلاف. دليل التثبيت والمرجع باللغة الإنجليزية.</sub>
