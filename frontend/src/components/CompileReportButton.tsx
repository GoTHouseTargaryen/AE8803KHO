"use client";

import { useSimStore } from "@/store/useSimStore";
import { compileReport } from "@/lib/api";

export default function CompileReportButton() {
  const taggedRuns = useSimStore((s) => s.taggedRuns);
  const reportStatus = useSimStore((s) => s.reportStatus);
  const reportUrl = useSimStore((s) => s.reportUrl);
  const reportError = useSimStore((s) => s.reportError);
  const setReportStatus = useSimStore((s) => s.setReportStatus);
  const setReportUrl = useSimStore((s) => s.setReportUrl);
  const setReportError = useSimStore((s) => s.setReportError);

  async function handleCompile() {
    if (taggedRuns.length === 0) return;
    setReportStatus("compiling");
    setReportUrl(null);
    setReportError(null);
    try {
      const blob = await compileReport(taggedRuns);
      const url = URL.createObjectURL(blob);
      setReportUrl(url);
      setReportStatus("done");
      const a = document.createElement("a");
      a.href = url;
      a.download = "report.pdf";
      a.click();
    } catch (err) {
      setReportError(err instanceof Error ? err.message : String(err));
      setReportStatus("error");
    }
  }

  const disabled = taggedRuns.length === 0 || reportStatus === "compiling";

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        className={`px-4 py-2 rounded text-sm font-semibold transition-colors ${
          disabled
            ? "bg-gray-700 text-gray-500 cursor-not-allowed"
            : "bg-indigo-600 text-white hover:bg-indigo-700"
        }`}
        onClick={handleCompile}
        disabled={disabled}
        title={
          taggedRuns.length === 0
            ? "Tag at least one run to compile the report"
            : "Compile AIAA PDF report"
        }
      >
        {reportStatus === "compiling"
          ? "Compiling... (may take ~30s)"
          : reportStatus === "done"
          ? "Re-compile Report"
          : "Compile Report (PDF)"}
      </button>

      {reportStatus === "done" && reportUrl && (
        <a
          href={reportUrl}
          download="report.pdf"
          className="text-xs text-green-400 hover:text-green-300 underline"
        >
          Download report.pdf
        </a>
      )}

      {reportStatus === "error" && reportError && (
        <p className="text-xs text-red-400 max-w-xs text-right" title={reportError}>
          Error: {reportError.slice(0, 80)}{reportError.length > 80 ? "..." : ""}
        </p>
      )}
    </div>
  );
}
