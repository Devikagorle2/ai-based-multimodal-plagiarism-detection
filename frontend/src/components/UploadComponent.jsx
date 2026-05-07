export default function UploadComponent({
  fileName,
  onFileChange,
  onClearFile,
  onClearText,
}) {
  return (
    <div className="mt-4 rounded-xl border border-dashed border-gray-300 bg-gray-50/50 p-4 transition-opacity duration-300">
      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">File upload</p>
      <p className="text-sm text-gray-600">
        {fileName ? <span className="font-medium text-gray-900">{fileName}</span> : "No file selected (.txt, .pdf, .docx)"}
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <label className="inline-flex cursor-pointer items-center justify-center rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm transition duration-200 hover:border-[#16a34a]/40 hover:bg-emerald-50/50">
          <input type="file" accept=".txt,.pdf,.docx" className="hidden" onChange={onFileChange} />
          Upload file
        </label>
        <button
          type="button"
          onClick={onClearText}
          className="rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm transition duration-200 hover:border-gray-300 hover:bg-gray-50"
        >
          Clear Text
        </button>
        {fileName && (
          <button
            type="button"
            onClick={onClearFile}
            className="rounded-lg px-3 py-2 text-sm text-gray-500 underline-offset-2 transition hover:text-gray-800 hover:underline"
          >
            Clear file
          </button>
        )}
      </div>
    </div>
  );
}
