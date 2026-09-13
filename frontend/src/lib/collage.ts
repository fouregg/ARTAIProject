/**
 * Раскладка коллажа: ровная сетка, у которой неполным может быть только последний ряд.
 *
 * Число колонок подбирается под пропорции экрана, чтобы плитка была близка к квадрату:
 * холст в зале книжный, но страница галереи и мини-полотно на терминале — альбомные,
 * поэтому число колонок считается от реальных размеров области, а не задаётся числом.
 *
 * Раньше остаток размазывался по всем рядам, и на книжном экране это давало заметный
 * вертикальный разлом посередине: часть рядов по шесть плиток, часть по пять. Ровная
 * сетка с центрированным хвостом читается как законченный коллаж.
 *
 * Общая для холста и для мини-полотна: миниатюра должна повторять то, что человек
 * видит на стене.
 */

/** Неровный хвост заметен глазом, поэтому делители count получают небольшую фору. */
const RAGGED_PENALTY = 0.18;

export function columnsFor(count: number, width: number, height: number): number {
  if (count <= 0) return 1;

  let best = 1;
  let bestCost = Number.POSITIVE_INFINITY;

  for (let columns = 1; columns <= count; columns += 1) {
    const rows = Math.ceil(count / columns);
    const tileWidth = Math.max(width, 1) / columns;
    const tileHeight = Math.max(height, 1) / rows;
    // Логарифм отношения сторон: 2:1 и 1:2 одинаково плохи.
    const squareness = Math.abs(Math.log(tileWidth / tileHeight));
    const cost = squareness + (count % columns === 0 ? 0 : RAGGED_PENALTY);

    if (cost < bestCost) {
      bestCost = cost;
      best = columns;
    }
  }

  return best;
}

/** Длины рядов сверху вниз: все по columns, последний — остаток. */
export function splitIntoRows(count: number, width: number, height: number): number[] {
  if (count <= 0) return [];

  const columns = columnsFor(count, width, height);
  const full = Math.floor(count / columns);
  const tail = count % columns;

  const rows = Array.from({ length: full }, () => columns);
  if (tail > 0) rows.push(tail);
  return rows;
}

/**
 * Номер текущей страницы холста, отсчитанный от часов.
 *
 * Экран в зале и миниатюра на терминале считают его одинаково, поэтому показывают
 * одну и ту же страницу без всякой синхронизации между собой.
 *
 * Каждая страница висит минуту, последняя — пять: на ней самые свежие работы.
 * Те же числа — в backend/app/api/routes/dome.py.
 */
export const PAGE_SIZE = 50;
export const PAGE_INTERVAL_MS = 60000;
export const LAST_PAGE_INTERVAL_MS = 300000;

export function currentPage(pageCount: number, now: number = Date.now()): number {
  if (pageCount <= 1) return 0;
  const cycle = (pageCount - 1) * PAGE_INTERVAL_MS + LAST_PAGE_INTERVAL_MS;
  // Хвост цикла длиннее минуты целиком приходится на последнюю страницу.
  return Math.min(Math.floor((now % cycle) / PAGE_INTERVAL_MS), pageCount - 1);
}
