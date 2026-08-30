/**
 * Фирменные знаки.
 *
 * Наверху — знак самого события, внизу — оператор сервиса (АНО «Таврида.Арт»)
 * и грантодатель (ПФКИ): его показ предусмотрен условиями гранта, см. согласие
 * на обработку персональных данных.
 */

export function EventLogo() {
  return (
    <img
      className="brand__event"
      src="/brand/mfm.svg"
      alt="Международный фестиваль молодёжи 2026"
    />
  );
}

export function BrandFooter() {
  return (
    <footer className="brandbar">
      <img className="brandbar__mark" src="/brand/tavrida.webp" alt="Таврида.Арт" />
      <img
        className="brandbar__mark brandbar__mark--wide"
        src="/brand/pfki.svg"
        alt="Президентский фонд культурных инициатив"
      />
    </footer>
  );
}
