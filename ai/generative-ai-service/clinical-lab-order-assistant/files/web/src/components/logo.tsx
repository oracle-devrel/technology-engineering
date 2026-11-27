export function LogoMark({ size = 30 }: { size?: number }) {
  return <svg viewBox="0 0 32 32" width={size} height={size} aria-hidden="true">
    <defs><linearGradient id="labsense-gradient" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#0a7cd5"/><stop offset="1" stopColor="#13b088"/></linearGradient></defs>
    <rect width="32" height="32" rx="9" fill="url(#labsense-gradient)"/>
    <path d="M16 6.5c-3.2 4.6-6.3 8-6.3 11.9a6.3 6.3 0 0 0 12.6 0C22.3 14.5 19.2 11.1 16 6.5z" fill="#fff" opacity=".96"/>
    <path d="M13.9 18.4h4.2M16 16.3v4.2" stroke="#0a7cd5" strokeWidth="1.7" strokeLinecap="round"/>
  </svg>;
}

export function initials(name: string) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]?.toUpperCase() ?? "").join("");
}
export function avatarClass(mrn: string) {
  let hash = 0; for (const ch of mrn) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return `avatar avatar-${hash % 5}`;
}
