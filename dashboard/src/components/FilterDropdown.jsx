import { useState, useRef, useEffect } from 'react'

export default function FilterDropdown({ icon, label, value, options, onChange }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  // Close on outside click
  useEffect(() => {
    if (!open) return
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  function select(opt) {
    onChange(opt)
    setOpen(false)
  }

  const isActive = open

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors text-left ${
          isActive
            ? 'bg-primary text-white'
            : 'bg-surface-container-low text-primary hover:bg-surface-container'
        }`}
      >
        <span className="material-symbols-outlined text-lg flex-shrink-0">{icon}</span>
        <div className="flex flex-col flex-1 min-w-0">
          <span className={`text-[9px] uppercase tracking-widest font-bold ${isActive ? 'opacity-70' : 'opacity-60'}`}>
            {label}
          </span>
          <span className={`text-sm font-semibold truncate ${isActive ? 'text-white' : 'text-on-surface'}`}>
            {value}
          </span>
        </div>
        <span
          className={`material-symbols-outlined text-sm flex-shrink-0 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        >
          expand_more
        </span>
      </button>

      {open && (
        <div className="absolute left-0 right-0 top-full mt-1 bg-surface-container-lowest rounded-xl shadow-ambient border border-outline-variant/20 z-50 overflow-hidden">
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => select(opt)}
              className={`w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center justify-between ${
                opt === value
                  ? 'bg-primary/8 text-primary font-semibold'
                  : 'text-on-surface hover:bg-surface-container-low'
              }`}
            >
              <span>{opt}</span>
              {opt === value && (
                <span className="material-symbols-outlined text-sm text-primary">check</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
