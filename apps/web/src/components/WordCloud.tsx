"use client";

type Word = { term: string; count: number; score: number };

export function WordCloud({ words }: { words: Word[] }) {
  const cleaned = words
    .filter((w) => w.term.trim().length >= 3 && !looksBroken(w.term))
    .slice(0, 28);
  if (!cleaned.length) {
    return <p className="empty">Update to see the language people use.</p>;
  }
  const max = Math.max(...cleaned.map((w) => w.score || w.count), 1);
  return (
    <div className="word-cloud" role="list" aria-label="Word cloud of common phrases">
      {cleaned.map((w, i) => {
        const weight = (w.score || w.count) / max;
        const size = 12 + Math.round(weight * 22);
        const tone = i % 5 === 0 ? "heat" : i % 3 === 0 ? "muted" : "base";
        return (
          <span
            role="listitem"
            key={w.term}
            className={`cloud-word cloud-${tone}`}
            style={{ fontSize: `${size}px`, fontWeight: weight > 0.65 ? 700 : weight > 0.35 ? 600 : 500 }}
            title={`${w.term} · ${w.count}`}
          >
            {w.term}
          </span>
        );
      })}
    </div>
  );
}

/** Drop tokenizer scraps like "arge anguage" / "anguage odels". */
function looksBroken(term: string): boolean {
  return term.split(/\s+/).some((part) => /^(arge|anguage|odels|odel|ature|anguage)$/i.test(part));
}
