/** Embeds dashboard/public/NSE Deck.html via Vite public URL. */

const DECK_HTML = encodeURIComponent('NSE Deck.html');

export default function NSEDeck() {
  return (
    <iframe
      src={`/${DECK_HTML}`}
      className="w-full border-0"
      style={{ height: 'calc(100vh - 64px)' }}
      title="NSE Deck presentation"
    />
  );
}
