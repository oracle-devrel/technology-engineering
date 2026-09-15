/**
 * Format an ISO date string as a compact relative time: 5m, 3h, 2d, 3w, 4mo, 2y.
 * Returns empty string for invalid dates.
 */
export function formatRelativeTime(isoDate) {
  if (!isoDate) return '';
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return '';
  const diffMs = Date.now() - date.getTime();
  const sec = Math.max(0, Math.round(diffMs / 1000));
  if (sec < 60) return 'now';
  const min = Math.round(sec / 60);
  if (min < 60) return `${min}m`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr}h`;
  const day = Math.round(hr / 24);
  if (day < 7) return `${day}d`;
  const week = Math.round(day / 7);
  if (week < 5) return `${week}w`;
  const month = Math.round(day / 30);
  if (month < 12) return `${month}mo`;
  const year = Math.round(day / 365);
  return `${year}y`;
}
