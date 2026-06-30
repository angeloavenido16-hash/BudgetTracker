export default function Spinner({ text = "Loading…" }: { text?: string }) {
  return (
    <div className="spinner-wrap">
      <div className="spinner" />
      {text && <span className="spinner-text">{text}</span>}
    </div>
  );
}
