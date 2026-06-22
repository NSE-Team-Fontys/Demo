// Theme accent color mapping — each of the 7 themes gets a signature palette
// Used for card borders, gradients, bar charts, and word cloud styling

export const THEME_COLORS = {
  content_org: {
    accent: '#002F59',
    accentLight: '#d3e3ff',
    gradient: 'linear-gradient(135deg, #002F59 0%, #0a4a8a 100%)',
    bgTint: 'rgba(0, 47, 89, 0.04)',
    bgHover: 'rgba(0, 47, 89, 0.08)',
    border: 'rgba(0, 47, 89, 0.15)',
  },
  link_practice: {
    accent: '#006A6A',
    accentLight: '#90efef',
    gradient: 'linear-gradient(135deg, #006A6A 0%, #0a8f8f 100%)',
    bgTint: 'rgba(0, 106, 106, 0.04)',
    bgHover: 'rgba(0, 106, 106, 0.08)',
    border: 'rgba(0, 106, 106, 0.15)',
  },
  teachers: {
    accent: '#7B3AED',
    accentLight: '#ede9fe',
    gradient: 'linear-gradient(135deg, rgb(123 58 237) 0%, rgb(123 85 247) 100%)',
    bgTint: 'rgba(123, 58, 237, 0.04)',
    bgHover: 'rgba(123, 58, 237, 0.08)',
    border: 'rgba(123, 58, 237, 0.15)',
  },
  support: {
    accent: '#059669',
    accentLight: '#d1fae5',
    gradient: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
    bgTint: 'rgba(5, 150, 105, 0.04)',
    bgHover: 'rgba(5, 150, 105, 0.08)',
    border: 'rgba(5, 150, 105, 0.15)',
  },
  examination: {
    accent: '#D97706',
    accentLight: '#fef3c7',
    gradient: 'linear-gradient(135deg, #D97706 0%, #f59e0b 100%)',
    bgTint: 'rgba(217, 119, 6, 0.04)',
    bgHover: 'rgba(217, 119, 6, 0.08)',
    border: 'rgba(217, 119, 6, 0.15)',
  },
  engagement: {
    accent: '#DC2626',
    accentLight: '#fee2e2',
    gradient: 'linear-gradient(135deg, #DC2626 0%, #ef4444 100%)',
    bgTint: 'rgba(220, 38, 38, 0.04)',
    bgHover: 'rgba(220, 38, 38, 0.08)',
    border: 'rgba(220, 38, 38, 0.15)',
  },
  special_circumstances: {
    accent: '#2563EB',
    accentLight: '#dbeafe',
    gradient: 'linear-gradient(135deg, #2563EB 0%, #3b82f6 100%)',
    bgTint: 'rgba(37, 99, 235, 0.04)',
    bgHover: 'rgba(37, 99, 235, 0.08)',
    border: 'rgba(37, 99, 235, 0.15)',
  },
}

// Ordered list for bar chart / consistent ordering
export const THEME_COLOR_LIST = [
  '#002F59', '#006A6A', '#7B3AED', '#059669', '#D97706', '#DC2626', '#2563EB',
]

export function getThemeColor(themeId) {
  return THEME_COLORS[themeId] || THEME_COLORS.content_org
}
