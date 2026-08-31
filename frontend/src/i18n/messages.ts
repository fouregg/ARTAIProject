import type { LanguageChoice } from "../api/client";

export const UI_LANGUAGES = ["ru", "en", "zh", "fr", "es", "pt", "ar"] as const;
export type UiLanguage = (typeof UI_LANGUAGES)[number];

export const RTL_LANGUAGES: readonly string[] = ["ar"];

export const LANGUAGE_NAMES: Record<UiLanguage, string> = {
  ru: "Русский",
  en: "English",
  zh: "中文",
  fr: "Français",
  es: "Español",
  pt: "Português",
  ar: "العربية",
};

export interface Messages {
  title: string;
  subtitle: string;
  placeholder: string;
  generate: string;
  stageQueued: string;
  stageTranslating: string;
  stageGenerating: string;
  again: string;
  editPrompt: string;
  save: string;
  saved: string;
  display: string;
  displayed: string;
  close: string;
  gallery: string;
  galleryTitle: string;
  galleryEmpty: string;
  back: string;
  delete: string;
  errorTitle: string;
  emptyPrompt: string;
  detectedAs: string;
  degraded: string;
  ttlHint: string;
  codeTitle: string;
  codeSubtitle: string;
  codeSubmit: string;
  signingIn: string;
  remaining: string;
  exhausted: string;
  logout: string;
  takesUpTo: string;
  secondsSuffix: string;
}

export const MESSAGES: Record<UiLanguage, Messages> = {
  ru: {
    title: "Генератор изображений",
    subtitle: "Опишите картинку на любом из семи языков — перевод сделаем сами",
    placeholder: "Например: рыжий кот в скафандре на фоне туманности",
    generate: "Сгенерировать",
    stageQueued: "В очереди…",
    stageTranslating: "Переводим запрос…",
    stageGenerating: "Рисуем изображение…",
    again: "Сгенерировать снова",
    editPrompt: "Изменить промпт",
    save: "Сохранить в галерею",
    saved: "Сохранено ✓",
    display: "Отобразить на цифровом холсте",
    displayed: "Отправлено на цифровой холст ✓",
    close: "Закрыть",
    gallery: "Галерея",
    galleryTitle: "Галерея",
    galleryEmpty: "Здесь пока пусто",
    back: "Назад",
    delete: "Удалить",
    errorTitle: "Не получилось",
    emptyPrompt: "Введите описание изображения",
    detectedAs: "Определён язык",
    degraded: "Перевод не удался — запрос ушёл как есть",
    ttlHint: "Хранится до {time}. Сохраните в галерею или отправьте на цифровой холст, чтобы не удалилось.",
    takesUpTo: "Модель рисует 30–90 секунд — это нормально",
    secondsSuffix: "с",
    codeTitle: "Введите код доступа",
    codeSubtitle: "5 цифр с вашего билета",
    codeSubmit: "Войти",
    signingIn: "Проверяем…",
    remaining: "Осталось генераций: {n}",
    exhausted: "Генерации по этому коду закончились",
    logout: "Выйти",
  },
  en: {
    title: "Image generator",
    subtitle: "Describe a picture in any of seven languages — we handle the translation",
    placeholder: "For example: a ginger cat in a spacesuit against a nebula",
    generate: "Generate",
    stageQueued: "Queued…",
    stageTranslating: "Translating the prompt…",
    stageGenerating: "Painting the image…",
    again: "Generate again",
    editPrompt: "Edit the prompt",
    save: "Save to gallery",
    saved: "Saved ✓",
    display: "Show on the digital canvas",
    displayed: "Sent to the digital canvas ✓",
    close: "Close",
    gallery: "Gallery",
    galleryTitle: "Gallery",
    galleryEmpty: "Nothing here yet",
    back: "Back",
    delete: "Delete",
    errorTitle: "Something went wrong",
    emptyPrompt: "Enter an image description",
    detectedAs: "Detected language",
    degraded: "Translation failed — the original text was used",
    ttlHint: "Kept until {time}. Save it to the gallery or send it to the digital canvas to keep it for good.",
    takesUpTo: "The model takes 30–90 seconds — that is normal",
    secondsSuffix: "s",
    codeTitle: "Enter your access code",
    codeSubtitle: "5 digits from your ticket",
    codeSubmit: "Sign in",
    signingIn: "Checking…",
    remaining: "Generations left: {n}",
    exhausted: "This code has no generations left",
    logout: "Sign out",
  },
  zh: {
    title: "图像生成器",
    subtitle: "用七种语言中的任意一种描述画面，翻译交给我们",
    placeholder: "例如：一只穿着宇航服的橘猫，背景是星云",
    generate: "生成",
    stageQueued: "排队中…",
    stageTranslating: "正在翻译…",
    stageGenerating: "正在绘制…",
    again: "重新生成",
    editPrompt: "修改提示词",
    save: "保存到图库",
    saved: "已保存 ✓",
    display: "显示在数字画布上",
    displayed: "已发送到数字画布 ✓",
    close: "关闭",
    gallery: "图库",
    galleryTitle: "图库",
    galleryEmpty: "这里还是空的",
    back: "返回",
    delete: "删除",
    errorTitle: "出错了",
    emptyPrompt: "请输入图像描述",
    detectedAs: "识别语言",
    degraded: "翻译失败，已使用原文",
    ttlHint: "保存至 {time}。保存到图库或发送到数字画布即可永久保留。",
    takesUpTo: "模型绘制需要 30–90 秒，属于正常",
    secondsSuffix: "秒",
    codeTitle: "请输入访问码",
    codeSubtitle: "门票上的 5 位数字",
    codeSubmit: "登录",
    signingIn: "验证中…",
    remaining: "剩余生成次数：{n}",
    exhausted: "此访问码的生成次数已用完",
    logout: "退出",
  },
  fr: {
    title: "Générateur d'images",
    subtitle: "Décrivez une image dans l'une des sept langues — la traduction est pour nous",
    placeholder: "Par exemple : un chat roux en combinaison spatiale devant une nébuleuse",
    generate: "Générer",
    stageQueued: "En file d'attente…",
    stageTranslating: "Traduction de la requête…",
    stageGenerating: "Création de l'image…",
    again: "Générer à nouveau",
    editPrompt: "Modifier la requête",
    save: "Enregistrer dans la galerie",
    saved: "Enregistré ✓",
    display: "Afficher sur la toile numérique",
    displayed: "Envoyé sur la toile numérique ✓",
    close: "Fermer",
    gallery: "Galerie",
    galleryTitle: "Galerie",
    galleryEmpty: "Rien pour l'instant",
    back: "Retour",
    delete: "Supprimer",
    errorTitle: "Échec",
    emptyPrompt: "Saisissez une description d'image",
    detectedAs: "Langue détectée",
    degraded: "Échec de la traduction — le texte original a été utilisé",
    ttlHint: "Conservée jusqu'à {time}. Enregistrez-la dans la galerie ou envoyez-la sur la toile numérique pour la garder.",
    takesUpTo: "Le modèle met 30 à 90 secondes — c'est normal",
    secondsSuffix: "s",
    codeTitle: "Saisissez votre code d'accès",
    codeSubtitle: "5 chiffres figurant sur votre billet",
    codeSubmit: "Se connecter",
    signingIn: "Vérification…",
    remaining: "Générations restantes : {n}",
    exhausted: "Ce code n'a plus de générations",
    logout: "Se déconnecter",
  },
  es: {
    title: "Generador de imágenes",
    subtitle: "Describe una imagen en cualquiera de los siete idiomas: la traducción es cosa nuestra",
    placeholder: "Por ejemplo: un gato naranja con traje espacial frente a una nebulosa",
    generate: "Generar",
    stageQueued: "En cola…",
    stageTranslating: "Traduciendo la petición…",
    stageGenerating: "Creando la imagen…",
    again: "Generar de nuevo",
    editPrompt: "Editar la petición",
    save: "Guardar en la galería",
    saved: "Guardado ✓",
    display: "Mostrar en el lienzo digital",
    displayed: "Enviado al lienzo digital ✓",
    close: "Cerrar",
    gallery: "Galería",
    galleryTitle: "Galería",
    galleryEmpty: "Aquí todavía no hay nada",
    back: "Volver",
    delete: "Eliminar",
    errorTitle: "Algo salió mal",
    emptyPrompt: "Introduce una descripción de la imagen",
    detectedAs: "Idioma detectado",
    degraded: "La traducción falló: se usó el texto original",
    ttlHint: "Se conserva hasta las {time}. Guárdala en la galería o envíala al lienzo digital para conservarla.",
    takesUpTo: "El modelo tarda entre 30 y 90 segundos: es normal",
    secondsSuffix: "s",
    codeTitle: "Introduce tu código de acceso",
    codeSubtitle: "5 dígitos de tu entrada",
    codeSubmit: "Entrar",
    signingIn: "Comprobando…",
    remaining: "Generaciones restantes: {n}",
    exhausted: "Este código ya no tiene generaciones",
    logout: "Salir",
  },
  pt: {
    title: "Gerador de imagens",
    subtitle: "Descreva uma imagem em qualquer um dos sete idiomas — a tradução é connosco",
    placeholder: "Por exemplo: um gato ruivo de fato espacial diante de uma nebulosa",
    generate: "Gerar",
    stageQueued: "Na fila…",
    stageTranslating: "A traduzir o pedido…",
    stageGenerating: "A criar a imagem…",
    again: "Gerar novamente",
    editPrompt: "Editar o pedido",
    save: "Guardar na galeria",
    saved: "Guardado ✓",
    display: "Mostrar na tela digital",
    displayed: "Enviado para a tela digital ✓",
    close: "Fechar",
    gallery: "Galeria",
    galleryTitle: "Galeria",
    galleryEmpty: "Ainda não há nada aqui",
    back: "Voltar",
    delete: "Eliminar",
    errorTitle: "Não resultou",
    emptyPrompt: "Introduza uma descrição da imagem",
    detectedAs: "Idioma detetado",
    degraded: "A tradução falhou — foi usado o texto original",
    ttlHint: "Guardada até às {time}. Guarde na galeria ou envie para a tela digital para a manter.",
    takesUpTo: "O modelo demora 30 a 90 segundos — é normal",
    secondsSuffix: "s",
    codeTitle: "Introduza o seu código de acesso",
    codeSubtitle: "5 dígitos do seu bilhete",
    codeSubmit: "Entrar",
    signingIn: "A verificar…",
    remaining: "Gerações restantes: {n}",
    exhausted: "Este código já não tem gerações",
    logout: "Sair",
  },
  ar: {
    title: "مولّد الصور",
    subtitle: "صف الصورة بأي من اللغات السبع، والترجمة علينا",
    placeholder: "مثال: قط برتقالي يرتدي بدلة فضاء أمام سديم",
    generate: "إنشاء",
    stageQueued: "في الانتظار…",
    stageTranslating: "جارٍ ترجمة الطلب…",
    stageGenerating: "جارٍ رسم الصورة…",
    again: "إنشاء مرة أخرى",
    editPrompt: "تعديل الطلب",
    save: "حفظ في المعرض",
    saved: "تم الحفظ ✓",
    display: "العرض على اللوحة الرقمية",
    displayed: "أُرسلت إلى اللوحة الرقمية ✓",
    close: "إغلاق",
    gallery: "المعرض",
    galleryTitle: "المعرض",
    galleryEmpty: "لا يوجد شيء هنا بعد",
    back: "رجوع",
    delete: "حذف",
    errorTitle: "حدث خطأ",
    emptyPrompt: "أدخل وصفًا للصورة",
    detectedAs: "اللغة المكتشفة",
    degraded: "تعذّرت الترجمة — استُخدم النص الأصلي",
    ttlHint: "محفوظة حتى {time}. احفظها في المعرض أو أرسلها إلى اللوحة الرقمية للاحتفاظ بها.",
    takesUpTo: "يستغرق النموذج من 30 إلى 90 ثانية — هذا طبيعي",
    secondsSuffix: "ث",
    codeTitle: "أدخل رمز الدخول",
    codeSubtitle: "5 أرقام من تذكرتك",
    codeSubmit: "دخول",
    signingIn: "جارٍ التحقق…",
    remaining: "الجيل المتبقي: {n}",
    exhausted: "لم تعد هناك عمليات إنشاء لهذا الرمز",
    logout: "خروج",
  },
};

/** Языки, между которыми переключает тумблер в шапке. */
export const TOGGLE_LANGUAGES = ["ru", "en"] as const;

/**
 * Язык интерфейса. По умолчанию русский: язык браузера не спрашиваем, иначе
 * у гостя с английской локалью интерфейс молча уезжал в английский.
 * Словари остальных языков сохранены — их можно включить, расширив тумблер.
 */
export function resolveUiLanguage(choice: LanguageChoice): UiLanguage {
  return choice === "auto" ? "ru" : choice;
}

export function isRtl(language: string): boolean {
  return RTL_LANGUAGES.includes(language);
}
