export const BRIN_TO_CITY = {
  '0': 'Eindhoven',
  '2': 'Meijerijstad',
  '3': 'Venlo',
  '4': 'Sittard-geleen',
  '8': 's-Hertogenbosch',
  '13': 'Tilburg',
  '20': 'Bergen op Zoom',
  '23': 'Rotterdam',
  '24': 'Utrecht',
  '26': 'Nijmegen',
}

export const CITY_TO_BRIN = Object.fromEntries(
  Object.entries(BRIN_TO_CITY).map(([code, city]) => [city, code])
)

export const LOCATION_OPTIONS = ['All', ...Object.values(BRIN_TO_CITY)]
