import { useState, useRef, useEffect } from 'react';
import { HelpCircle, X } from 'lucide-react';

interface InfoLine {
  label: string;
  value: string;
  color?: string;
}

interface Props {
  lines: InfoLine[];
}

export default function InfoTip({ lines }: Props) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ top: 0, left: 0 });
  const btnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open && btnRef.current) {
      const rect = btnRef.current.getBoundingClientRect();
      const popupW = 320;
      let left = rect.right - popupW;
      if (left < 8) left = 8;
      let top = rect.bottom + 6;
      if (top + 150 > window.innerHeight) top = rect.top - 150;
      setPos({ top, left });
    }
  }, [open]);

  return (
    <>
      <button ref={btnRef} onClick={() => setOpen(!open)}
        className="w-5 h-5 rounded-full border border-dark-700 flex items-center justify-center text-gray-500 hover:text-oracle-red hover:border-oracle-red/30 transition-colors shrink-0">
        <HelpCircle size={12} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-[60]" onClick={() => setOpen(false)} />
          <div className="fixed z-[70] w-80 bg-dark-800 border border-dark-700 rounded-lg shadow-2xl"
            style={{ top: pos.top, left: pos.left }}>
            <div className="flex items-center justify-between px-3 pt-2.5 pb-1">
              <span className="text-[11px] text-gray-500 uppercase tracking-wider font-medium">Details</span>
              <button onClick={() => setOpen(false)} className="text-gray-600 hover:text-white"><X size={12} /></button>
            </div>
            <div className="px-3 pb-3 space-y-1.5">
              {lines.map(({ label, value, color }) => (
                <div key={label}>
                  <span className={`text-[11px] font-semibold ${color || 'text-oracle-red'}`}>{label}: </span>
                  <span className="text-[11px] text-gray-400">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </>
  );
}
