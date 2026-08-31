/**
 * Приведение цифр к латинским.
 *
 * Гость может набрать код любой раскладкой: китайская в полноширинном режиме даёт
 * «５０１７９», арабская — «٥٠١٧٩». Регулярка /\D/ считает такие символы не-цифрами
 * и молча их стирала, из-за чего поле кода оставалось пустым, а если значение всё же
 * доходило до сервера — гость видел «Неверный код».
 */

// Полноширинные ０-９ разбирает сама нормализация NFKC, а арабские ряды — нет.
const DIGIT_RANGES: ReadonlyArray<readonly [number, number]> = [
  [0x0660, 0x0669], // арабо-индийские ٠-٩
  [0x06f0, 0x06f9], // восточные арабо-индийские ۰-۹
  [0x0966, 0x096f], // деванагари ०-९
];

export function toAsciiDigits(value: string): string {
  return Array.from(value.normalize("NFKC"))
    .map((char) => {
      const code = char.codePointAt(0) ?? 0;
      for (const [start, end] of DIGIT_RANGES) {
        if (code >= start && code <= end) return String(code - start);
      }
      return char;
    })
    .join("")
    .replace(/\D/g, "");
}
