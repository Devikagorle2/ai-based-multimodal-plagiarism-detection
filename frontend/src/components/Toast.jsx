export default function Toast({ message, onClose }) {
  if (!message) return null;
  return (
    <div
      className="fixed bottom-6 left-1/2 z-[100] -translate-x-1/2 animate-fade-in rounded-2xl bg-gray-900 px-6 py-3 text-sm font-medium text-white shadow-xl"
      role="status"
    >
      {message}
      <button type="button" onClick={onClose} className="ml-3 text-gray-300 hover:text-white">
        ×
      </button>
    </div>
  );
}
