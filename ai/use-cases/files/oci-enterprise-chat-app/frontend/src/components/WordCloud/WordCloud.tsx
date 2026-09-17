import React, { useEffect, useRef, useMemo } from 'react';
import { WordFrequency } from '../../types';

interface WordCloudProps {
  words: WordFrequency[];
  width?: number;
  height?: number;
}

// Oracle-red palette with variations
const COLORS = [
  '#C74634', // oracle-red
  '#E05A48', // oracle-red-light
  '#A33828', // oracle-red-dark
  '#E8826F', // lighter
  '#D4584A', // mid
  '#F09A8B', // pastel
  '#B84030', // deeper
  '#CC6B5C', // warm
];

interface PlacedWord {
  text: string;
  fontSize: number;
  x: number;
  y: number;
  color: string;
  rotation: number;
  width: number;
  height: number;
}

function doesOverlap(a: PlacedWord, b: PlacedWord): boolean {
  const pad = 4;
  return !(
    a.x + a.width + pad < b.x ||
    b.x + b.width + pad < a.x ||
    a.y + a.height + pad < b.y ||
    b.y + b.height + pad < a.y
  );
}

function layoutWords(
  words: WordFrequency[],
  canvasWidth: number,
  canvasHeight: number
): PlacedWord[] {
  if (words.length === 0) return [];

  const maxCount = words[0].count;
  const minCount = words[words.length - 1]?.count || 1;
  const range = Math.max(maxCount - minCount, 1);

  const placed: PlacedWord[] = [];
  const centerX = canvasWidth / 2;
  const centerY = canvasHeight / 2;

  for (let i = 0; i < words.length; i++) {
    const { word, count } = words[i];
    const normalized = (count - minCount) / range;
    const fontSize = Math.round(14 + normalized * 42);
    const rotation = i > 5 && Math.random() > 0.7 ? (Math.random() > 0.5 ? 90 : -90) : 0;

    // Estimate dimensions
    const charWidth = fontSize * 0.6;
    const wordWidth = rotation !== 0 ? fontSize * 1.2 : word.length * charWidth;
    const wordHeight = rotation !== 0 ? word.length * charWidth : fontSize * 1.3;

    const color = COLORS[i % COLORS.length];

    // Spiral placement
    let placed_word: PlacedWord | null = null;
    for (let r = 0; r < Math.max(canvasWidth, canvasHeight); r += 3) {
      for (let angle = 0; angle < 360; angle += 15) {
        const rad = (angle * Math.PI) / 180;
        const x = centerX + r * Math.cos(rad) - wordWidth / 2;
        const y = centerY + r * Math.sin(rad) - wordHeight / 2;

        // Check bounds
        if (x < 0 || y < 0 || x + wordWidth > canvasWidth || y + wordHeight > canvasHeight) {
          continue;
        }

        const candidate: PlacedWord = {
          text: word,
          fontSize,
          x,
          y,
          color,
          rotation,
          width: wordWidth,
          height: wordHeight,
        };

        const overlaps = placed.some((p) => doesOverlap(candidate, p));
        if (!overlaps) {
          placed_word = candidate;
          break;
        }
      }
      if (placed_word) break;
    }

    if (placed_word) {
      placed.push(placed_word);
    }
  }

  return placed;
}

const WordCloud: React.FC<WordCloudProps> = ({ words, width = 700, height = 400 }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  const placedWords = useMemo(
    () => layoutWords(words.slice(0, 80), width, height),
    [words, width, height]
  );

  return (
    <div ref={containerRef} className="relative" style={{ width, height }}>
      <svg width={width} height={height} className="select-none">
        {placedWords.map((w, i) => (
          <text
            key={`${w.text}-${i}`}
            x={w.x + w.width / 2}
            y={w.y + w.height / 2}
            textAnchor="middle"
            dominantBaseline="central"
            fill={w.color}
            fontSize={w.fontSize}
            fontWeight={w.fontSize > 35 ? 'bold' : w.fontSize > 25 ? '600' : 'normal'}
            fontFamily="Oracle Sans, Inter, system-ui, sans-serif"
            transform={w.rotation !== 0 ? `rotate(${w.rotation}, ${w.x + w.width / 2}, ${w.y + w.height / 2})` : undefined}
            opacity={0.85 + (w.fontSize / 56) * 0.15}
            className="transition-opacity hover:opacity-100"
          >
            {w.text}
          </text>
        ))}
      </svg>
    </div>
  );
};

export default WordCloud;
