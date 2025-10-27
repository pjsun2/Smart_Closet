import React, { useCallback, useMemo, useRef, useState } from "react";

/**
 * BLEU/ROUGE 평가 CSV 업로더 (React 단일 파일 컴포넌트)
 *
 * 요구사항:
 *  - CSV(id, question, reference) 업로드 → POST /api/voice/eval (multipart/form-data)
 *  - 서버 응답: { ok, result_csv, summary }
 *  - 요약 지표 표시 + 결과 CSV 다운로드 링크 제공
 *  - 드래그앤드롭/클릭 업로드, 로딩/에러 상태, 간단한 검증/프리뷰
 */
export default function EvalPage({ apiBase = "" }) {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null); // { result_csv, summary }
  const inputRef = useRef(null);

  const handlePick = useCallback(() => inputRef.current?.click(), []);

  const onFileChange = useCallback((e) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    const f = e.dataTransfer?.files?.[0];
    if (f) setFile(f);
  }, []);

  const onDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  }, []);

  const onDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }, []);

  const valid = useMemo(() => {
    if (!file) return false;
    return file.name.toLowerCase().endsWith(".csv");
  }, [file]);

  const handleUpload = useCallback(async () => {
    setError("");
    setResult(null);
    if (!file) {
      setError("CSV 파일을 선택해 주세요.");
      return;
    }
    if (!valid) {
      setError("CSV 확장자 파일만 업로드할 수 있습니다.");
      return;
    }

    const form = new FormData();
    form.append("file", file);

    setIsLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/voice/eval`, {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(data?.error || "업로드 중 오류가 발생했습니다.");
      }
      setResult({
        result_csv: data.result_csv, // 서버 상대 경로
        summary: data.summary,
      });
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setIsLoading(false);
    }
  }, [apiBase, file, valid]);

  const handleDownload = useCallback(() => {
    if (!result?.result_csv) return;
    // 서버가 절대 경로가 아니라 상대 경로를 주므로 apiBase와 합쳐줌
    const url = result.result_csv.startsWith("http")
      ? result.result_csv
      : `${apiBase}${result.result_csv}`;
    window.open(url, "_blank");
  }, [apiBase, result]);

  const downloadTemplate = useCallback(() => {
    const header = "id,question,reference\n";
    const rows = [
      '1,"겨울 회사 회식인데 깔끔하게","회식에는 니트와 슬랙스에 코트를 매치하면 깔끔합니다."',
      '2,"비 오는 날 데이트룩 추천","트렌치코트와 미디스커트 조합이 세련됩니다."',
      '3,"캠퍼스 개강파티 옷 추천","셔츠+데님+스니커즈로 편하고 단정하게 연출하세요."',
    ];
    const csv = header + rows.join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "eval_template.csv";
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800">
      <div className="max-w-4xl mx-auto p-6">
        <header className="mb-6">
          <h1 className="text-2xl font-bold">BLEU/ROUGE 평가 업로더</h1>
          <p className="text-sm text-gray-600 mt-1">
            CSV(id, question, reference)를 업로드하면 서버에서 챗봇 응답을 생성하여 BLEU/ROUGE를 계산하고 결과 CSV를 내려줍니다.
          </p>
        </header>

        {/* 업로드 카드 */}
        <div
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          className={`border-2 border-dashed rounded-2xl p-8 bg-white transition ${
            dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300"
          }`}
        >
          <div className="flex flex-col items-center gap-3 text-center">
            <div className="text-lg font-medium">CSV 파일 드래그앤드롭 또는 클릭 업로드</div>
            <div className="text-xs text-gray-500">필수 컬럼: id, question, reference</div>

            <input
              ref={inputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={onFileChange}
            />

            <div className="flex items-center gap-3 mt-2">
              <button
                onClick={handlePick}
                className="px-4 py-2 rounded-xl bg-gray-800 text-white hover:bg-gray-700"
              >
                파일 선택
              </button>
              <button
                onClick={downloadTemplate}
                className="px-4 py-2 rounded-xl bg-white border hover:bg-gray-50"
              >
                템플릿 받기
              </button>
            </div>

            {file && (
              <div className="mt-4 text-sm">
                <span className="font-semibold">선택됨:</span> {file.name}
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={!valid || isLoading}
              className={`mt-4 px-5 py-2.5 rounded-xl text-white transition ${
                isLoading
                  ? "bg-gray-400 cursor-not-allowed"
                  : valid
                  ? "bg-blue-600 hover:bg-blue-500"
                  : "bg-gray-400 cursor-not-allowed"
              }`}
            >
              {isLoading ? "업로드 중..." : "평가 실행"}
            </button>

            {error && (
              <div className="mt-3 text-red-600 text-sm">{error}</div>
            )}
          </div>
        </div>

        {/* 결과 카드 */}
        {result && (
          <div className="mt-8 bg-white rounded-2xl border p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">평가 결과</h2>
              <button
                onClick={handleDownload}
                className="px-4 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-500"
              >
                결과 CSV 다운로드
              </button>
            </div>

            {/* 요약 표 */}
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <Metric label="Rows" value={result.summary?.count ?? "-"} />
              <Metric label="BLEU-1" value={fmt(result.summary?.bleu1)} />
              <Metric label="BLEU-2" value={fmt(result.summary?.bleu2)} />
              <Metric label="BLEU-3" value={fmt(result.summary?.bleu3)} />
              <Metric label="BLEU-4" value={fmt(result.summary?.bleu4)} />
              <Metric label="ROUGE-1(F)" value={fmt(result.summary?.rouge1_f)} />
              <Metric label="ROUGE-2(F)" value={fmt(result.summary?.rouge2_f)} />
              <Metric label="ROUGE-L(F)" value={fmt(result.summary?.rougeL_f)} />
            </div>

            <p className="mt-3 text-xs text-gray-500">
              * elapsed_ms는 서버에서 한 샘플 생성에 걸린 평균 시간(ms)입니다.
            </p>
          </div>
        )}

        {/* 도움말 */}
        <div className="mt-8 text-xs text-gray-500 leading-6">
          <p>서버 엔드포인트: <code>{apiBase || ""}/api/voice/eval</code></p>
          <p>응답 JSON: {'{ ok, result_csv, summary }'}</p>
          <p>summary: {'{ bleu1, bleu2, bleu3, bleu4, rouge1_f, rouge2_f, rougeL_f, elapsed_ms }'}</p>
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="border rounded-xl p-3 bg-gray-50">
      <div className="text-[11px] uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-base font-semibold mt-1">{value}</div>
    </div>
  );
}

function fmt(n) {
  if (n === undefined || n === null || isNaN(Number(n))) return "-";
  return Number(n).toFixed(4);
}
