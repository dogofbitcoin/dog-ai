import { useState } from "react";

export default function Tabs({ tabs, defaultId, onChange }) {
  const initial = defaultId || tabs[0]?.id;
  const [active, setActive] = useState(initial);
  const current = tabs.find((t) => t.id === active) || tabs[0];

  const pick = (id) => {
    setActive(id);
    if (onChange) onChange(id);
  };

  return (
    <>
      <div className="tabs">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`tab${t.id === active ? " active" : ""}`}
            onClick={() => pick(t.id)}
            type="button"
          >
            {t.label}
            {t.badge ? <span className="tab-badge">{t.badge}</span> : null}
          </button>
        ))}
      </div>
      <div className="tab-body">{current?.render?.()}</div>
    </>
  );
}
