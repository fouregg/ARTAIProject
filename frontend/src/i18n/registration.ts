/**
 * Подписи экранов входа и анкеты участника.
 *
 * Здесь только русский и английский — те же языки, между которыми переключает
 * тумблер в шапке. Тексты самих согласий не переводятся сознательно: соглашение
 * действует в русской редакции (п. 13.2), а их формулировки приходят с бэкенда
 * из документа «Экранные тексты терминала».
 */
import { useI18n } from "./LanguageContext";

export interface RegistrationMessages {
  authOpen: string;
  tabLogin: string;
  tabRegister: string;
  codeLabel: string;
  codeHint: string;
  needAuth: string;
  notRegistered: string;
  registerSubmit: string;
  haveCode: string;
  noAccount: string;
  goLogin: string;
  goRegister: string;

  title: string;
  subtitle: string;

  lastName: string;
  firstName: string;
  middleName: string;
  birthDate: string;
  country: string;

  representative: string;
  agreementFull: string;
  consentFull: string;
  policy: string;

  submit: string;
  submitting: string;
  required: string;
  checkboxesRequired: string;
  loading: string;
  loadFailed: string;
}

const RU: RegistrationMessages = {
  authOpen: "Войти / Регистрация",
  tabLogin: "Вход",
  tabRegister: "Регистрация",
  codeLabel: "Код доступа",
  codeHint: "5 цифр с вашего билета",
  needAuth: "Чтобы отправить запрос, войдите или зарегистрируйтесь.",
  notRegistered: "У этого кода ещё нет анкеты — заполните её здесь.",
  registerSubmit: "Зарегистрироваться",
  haveCode: "Уже регистрировались?",
  noAccount: "Первый раз?",
  goLogin: "Войти по коду",
  goRegister: "Заполнить анкету",

  title: "Данные участника",
  subtitle: "Заполните форму, чтобы перейти к созданию изображения",

  lastName: "Фамилия",
  firstName: "Имя",
  middleName: "Отчество (при наличии)",
  birthDate: "Дата рождения",
  country: "Страна",

  representative:
    "Отмечаю за несовершеннолетнего: я его родитель или иной законный представитель",
  agreementFull: "Полный текст соглашения",
  consentFull: "Полный текст согласия",
  policy: "Политика обработки персональных данных",

  submit: "Продолжить",
  submitting: "Сохраняем…",
  required: "Заполните все обязательные поля",
  checkboxesRequired: "Чтобы продолжить, отметьте оба согласия",
  loading: "Загружаем тексты…",
  loadFailed: "Не удалось загрузить тексты соглашений",
};

const EN: RegistrationMessages = {
  authOpen: "Sign in / Register",
  tabLogin: "Sign in",
  tabRegister: "Register",
  codeLabel: "Access code",
  codeHint: "5 digits from your ticket",
  needAuth: "To send a request, sign in or register.",
  notRegistered: "There is no form for this code yet — fill it in here.",
  registerSubmit: "Register",
  haveCode: "Already registered?",
  noAccount: "First time here?",
  goLogin: "Sign in with a code",
  goRegister: "Fill in the form",

  title: "Participant details",
  subtitle: "Fill in the form to start creating images",

  lastName: "Last name",
  firstName: "First name",
  middleName: "Middle name (if any)",
  birthDate: "Date of birth",
  country: "Country",

  representative:
    "I am ticking on behalf of a minor: I am their parent or legal representative",
  agreementFull: "Full text of the agreement",
  consentFull: "Full text of the consent",
  policy: "Personal data processing policy",

  submit: "Continue",
  submitting: "Saving…",
  required: "Fill in all required fields",
  checkboxesRequired: "To continue, tick both consents",
  loading: "Loading the texts…",
  loadFailed: "Could not load the agreement texts",
};

export const REGISTRATION = { ru: RU, en: EN } as const;

export function useReg(): RegistrationMessages {
  const { uiLanguage } = useI18n();
  // Для языков, на которые подписи входа не переводились, английский понятнее русского.
  return uiLanguage === "ru" ? RU : EN;
}
