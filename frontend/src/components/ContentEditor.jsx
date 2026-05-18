import React, { useState } from 'react';

const MAX_CHARS = 55;

export default function ContentEditor({ initialItems = ['', '', ''], onChange }) {
  const [items, setItems] = useState(initialItems.length ? initialItems : ['', '', '']);

  const totalChars = items.reduce((sum, item) => sum + item.length, 0);

  function updateItem(index, value) {
    const next = items.map((item, i) => (i === index ? value : item));
    if (next.reduce((s, v) => s + v.length, 0) <= MAX_CHARS) {
      setItems(next);
      onChange?.(next);
    }
  }

  return (
    <div className="content-editor">
      <label className="content-editor-label">Content</label>
      <div className="content-editor-list">
        {items.map((item, idx) => (
          <div key={idx} className="content-editor-row">
            <span className="content-editor-num">{idx + 1}</span>
            <input
              type="text"
              className="content-editor-input"
              value={item}
              onChange={(e) => updateItem(idx, e.target.value)}
              placeholder={`Link ${idx + 1}`}
            />
          </div>
        ))}
      </div>
      <div className="content-editor-counter">
        {totalChars}/{MAX_CHARS} chars
      </div>
    </div>
  );
}
