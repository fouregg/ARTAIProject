/**
 * Раскладка коллажа: строками, а не жёсткой сеткой.
 *
 * Сетка repeat(N, 1fr) оставляет чёрные дыры, когда число картинок не делится на
 * число колонок. Здесь строки заполняются целиком при любом количестве плиток,
 * а число строк подбирается под пропорции области, чтобы плитки не вытягивались.
 *
 * Общая для холста и для мини-полотна на терминале: миниатюра должна повторять
 * то, что человек видит на стене.
 */
export function splitIntoRows(count: number, width: number, height: number): number[] {
  if (count === 0) return [];

  const rows = Math.max(1, Math.round(Math.sqrt((count * height) / Math.max(width, 1))));
  const base = Math.floor(count / rows);
  let extra = count % rows;

  return Array.from({ length: rows }, () => {
    const size = base + (extra > 0 ? 1 : 0);
    if (extra > 0) extra -= 1;
    return size;
  }).filter((size) => size > 0);
}

/**
 * Номер текущей страницы холста, отсчитанный от часов.
 *
 * Экран в зале и миниатюра на терминале считают его одинаково, поэтому показывают
 * одну и ту же страницу без всякой синхронизации между собой.
 */
export const PAGE_SIZE = 50;
export const PAGE_INTERVAL_MS = 60000;

export function currentPage(pageCount: number, now: number = Date.now()): number {
  if (pageCount <= 1) return 0;
  return Math.floor(now / PAGE_INTERVAL_MS) % pageCount;
}
