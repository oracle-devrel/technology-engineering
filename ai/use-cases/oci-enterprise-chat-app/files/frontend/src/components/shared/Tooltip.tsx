import { useState, useRef, type ReactNode } from 'react';

interface Props {
  text: string;
  children: ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
}

export default function Tooltip({ text, children, position = 'right', delay = 300 }: Props) {
  const [show, setShow] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleEnter = () => {
    timer.current = setTimeout(() => setShow(true), delay);
  };

  const handleLeave = () => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    setShow(false);
  };

  const posStyles: Record<string, React.CSSProperties> = {
    top: { bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: 8 },
    bottom: { top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: 8 },
    left: { right: '100%', top: '50%', transform: 'translateY(-50%)', marginRight: 8 },
    right: { left: '100%', top: '50%', transform: 'translateY(-50%)', marginLeft: 8 },
  };

  return (
    <div
      className="relative w-full"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
      {children}
      {show && (
        <div
          className="fixed z-[9999] px-2.5 py-1.5 bg-gray-900 border border-dark-700 text-gray-200 text-[11px] rounded-lg shadow-xl pointer-events-none"
          style={{
            ...posStyles[position],
            position: 'absolute',
            whiteSpace: text.length > 60 ? 'normal' : 'nowrap',
            maxWidth: 280,
          }}
        >
          {text}
        </div>
      )}
    </div>
  );
}
