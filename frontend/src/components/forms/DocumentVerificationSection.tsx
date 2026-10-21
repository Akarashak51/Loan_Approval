import { useCallback, useEffect, useState } from 'react';
import { CheckCircle2 } from 'lucide-react';
import { documentApi } from '../../services/api';
import type { DocumentRecord, DocumentType, VerificationReport } from '../../types';

const DOCUMENT_SLOTS: Array<{ type: DocumentType; title: string; required: boolean }> = [
  { type: 'AADHAAR_CARD', title: 'Aadhaar', required: true },
  { type: 'PAN_CARD', title: 'PAN Card', required: true },
  { type: 'SALARY_SLIP', title: 'Salary slip', required: false },
  { type: 'BANK_STATEMENT', title: 'Bank statement', required: true },
];
const SLOTS = DOCUMENT_SLOTS;

function isOcrCapabilityNotice(reason: string) {
  const normalized = reason.replace(/\s+/g, ' ').trim();
  return /Scanned PDFs require Poppler and Tesseract on PATH\.?/i.test(normalized) ||
    /OCR requires Tesseract\. Install Tesseract and add it to PATH\./i.test(normalized);
}

function hasVerificationResult(document?: DocumentRecord) {
  return !!document?.verification && ['VERIFIED', 'NEEDS_REVIEW', 'REJECTED', 'FAILED'].includes(document.verification.status);
}

export default function DocumentVerificationSection({ onReadinessChange }: { onReadinessChange?: (ready: boolean, errors?: string[]) => void }) {
  const [documents, setDocuments] = useState<Record<string, DocumentRecord>>({});
  const [report, setReport] = useState<VerificationReport | null>(null);
  const [uploading, setUploading] = useState<string | null>(null);
  const [removing, setRemoving] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [ocrCapabilityNotice, setOcrCapabilityNotice] = useState<string | null>(null);
  const refresh = useCallback(async () => {
    const docs = await documentApi.pending();
    setDocuments(Object.fromEntries(docs.map(d => [d.documentType, d])));
    const byType = Object.fromEntries(docs.map(document => [document.documentType, document]));
    const missing = SLOTS.filter(({ type, required }) => required && (
      (byType[type]?.status !== 'VERIFIED' && byType[type]?.verification?.status !== 'VERIFIED')
    )).map(({ title }) => `${title} is not approved.`);
    // Match the button gate to the same statuses rendered in the four cards.
    // The report endpoint remains informational and cannot leave an otherwise
    // complete form disabled if it is stale or temporarily unavailable.
    onReadinessChange?.(missing.length === 0, missing);
    try {
      setReport(await documentApi.report());
    } catch {
      setReport(null);
    }
  }, [onReadinessChange]);
  useEffect(() => { refresh().catch(() => { setErrors({ general: 'Could not load document report.' }); onReadinessChange?.(false); }); }, [refresh, onReadinessChange]);
  const upload = async (type: DocumentType, file?: File) => {
    if (!file) return;
    setUploadError(null);
    setErrors(prev => ({ ...prev, [type]: '' }));
    if (file.size > 5 * 1024 * 1024) {
      setUploadError(`${SLOTS.find(slot => slot.type === type)?.title}: Maximum file size is 5 MB.`); return;
    }
    setUploading(type); setProgress(0); onReadinessChange?.(false);
    try {
      const document = await documentApi.upload(type, file, true, setProgress);
      setDocuments(prev => ({ ...prev, [type]: document }));
    } catch (error: unknown) {
      const data = (error as { response?: { data?: { document?: DocumentRecord; message?: string; checks?: Array<{ status: string; reason: string }> } } }).response?.data;
      const reasons = data?.checks?.filter(c => c.status !== 'PASS').map(c => c.reason) ?? [];
      const capability = [...reasons, data?.message ?? ''].find(isOcrCapabilityNotice);
      if (capability) setOcrCapabilityNotice(capability);
      const message = reasons.filter(reason => !isOcrCapabilityNotice(reason)).join(' ') ||
        (data?.message && !isOcrCapabilityNotice(data.message) ? data.message : '');
      if (data?.document && hasVerificationResult(data.document)) {
        setDocuments(prev => ({ ...prev, [type]: data.document! }));
        setErrors(prev => ({ ...prev, [type]: message }));
      } else if (message || !capability) {
        setUploadError(`${SLOTS.find(slot => slot.type === type)?.title}: ${message || 'Upload failed. Please try again.'}`);
      }
    } finally {
      await refresh().catch(() => setErrors(prev => ({ ...prev, general: 'Could not refresh document report.' })));
      setUploading(null);
    }
  };
  const remove = async (type: DocumentType, id: number) => {
    setRemoving(type); onReadinessChange?.(false);
    setErrors(prev => ({ ...prev, [type]: '' }));
    try {
      await documentApi.remove(id);
    } catch (error: unknown) {
      const data = (error as { response?: { data?: { error?: string } } }).response?.data;
      setErrors(prev => ({ ...prev, [type]: data?.error ?? 'Could not remove this document. Please try again.' }));
    } finally {
      await refresh().catch(() => setErrors(prev => ({ ...prev, general: 'Could not refresh document report.' })));
      setRemoving(null);
    }
  };
  const capabilityNotice = [
    ocrCapabilityNotice ?? '',
    ...Object.values(documents).flatMap(document => document.verification?.mismatches ?? []),
    ...(report?.checks.map(check => check.reason) ?? []),
    ...(report?.reasons ?? []),
  ].find(isOcrCapabilityNotice);
  return <section className="rounded-xl border border-slate-200 bg-white p-5">
    <h2 className="text-lg font-semibold">Upload documents</h2>
    {capabilityNotice && <p role="status" className="mt-2 text-sm text-amber-800">{capabilityNotice}</p>}
    <p className="mt-2 text-sm text-slate-600">Aadhaar, PAN Card, and bank statement are required for the review. Salary slip stays optional but is included when available.</p>
    <p className="mt-2 text-sm text-slate-500">Use the applicant's own documents only. Mismatched names or wrong document types are rejected before analysis. PDF, PNG or JPG, up to 5 MB.</p>
    {errors.general && <p role="alert">{errors.general}</p>}
    {uploadError && <p role="alert" className="mt-2 text-sm text-red-700">{uploadError}</p>}
    <div className="mt-5 grid gap-4 md:grid-cols-2">{SLOTS.map(({ type, title, required }) => {
      const document = documents[type];
      const hasResult = hasVerificationResult(document);
      const approved = document?.status === 'VERIFIED' || document?.verification?.status === 'VERIFIED';
      const status = !document ? 'NOT UPLOADED' : !document.verification ? 'Uploaded' : document.verification.status === 'VERIFIED'
        ? 'VERIFIED'
        : document.verification.status === 'REJECTED'
          ? 'REJECTED'
          : document.verification.status === 'NEEDS_REVIEW'
            ? 'NEEDS_REVIEW'
            : document.verification.status === 'FAILED'
              ? 'FAILED'
              : document.status === 'VERIFYING' ? 'VERIFYING' : 'Uploaded';
      const identity = required;
      return <article key={type} className="rounded-lg border p-4">
        <div className="flex justify-between gap-2"><label htmlFor={`upload-${type}`} className="font-semibold">{title}{identity && <> <span className="text-red-600" aria-hidden="true">*</span><span className="sr-only">required</span></>}{!required && <span className="text-slate-500"> (optional)</span>}</label>
          <span className={`inline-flex items-center gap-1 rounded px-2 text-xs ${approved ? 'bg-green-100 text-green-800' : status === 'REJECTED' ? 'bg-red-100 text-red-800' : 'bg-slate-100 text-slate-700'}`}>{approved && <CheckCircle2 size={14} aria-hidden="true" />}{status}</span></div>
        <input id={`upload-${type}`} type="file" aria-required="true" accept={type === 'BANK_STATEMENT' ? '.pdf,.png,.jpg,.jpeg,.csv' : '.pdf,.png,.jpg,.jpeg'} disabled={!!uploading || !!removing}
          className="mt-3 block w-full text-sm" onChange={event => { void upload(type, event.target.files?.[0]); event.target.value = ''; }} />
        {approved && <p className="mt-2 inline-flex items-center gap-1 rounded bg-green-100 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-green-800"><CheckCircle2 size={12} aria-hidden="true" />{title} approved</p>}
        {document && <div className="mt-3 flex items-center justify-between gap-2"><p className="truncate text-xs text-slate-500">{document.filename}</p>
          <button type="button" aria-label={`Remove ${title}`} disabled={!!uploading || !!removing || document.documentStatus === 'approved' || document.documentStatus === 'rejected'} onClick={() => void remove(type, document.id)} className="rounded border border-red-200 px-3 py-1 text-sm font-semibold text-red-700 disabled:opacity-50">{removing === type ? 'Removing…' : 'Remove'}</button></div>}
        {uploading === type && <div className="mt-2"><progress aria-label={`${title} upload progress`} max={100} value={progress} /><p className="text-xs">{progress < 100 ? `${progress}% uploaded` : 'Extracting and checking document…'}</p></div>}
        {document && errors[type] && !isOcrCapabilityNotice(errors[type]) && <p role="alert" className="mt-2 text-sm text-red-700">{errors[type]}</p>}
        {hasResult && !approved && document.verification?.mismatches.filter(reason => !isOcrCapabilityNotice(reason) && reason !== errors[type]).map((reason, i) => <p key={i} className="mt-2 text-xs text-amber-800">{reason}</p>)}
      </article>;
    })}</div>
    {report?.documents && Object.keys(report.documents).length > 0 && <section aria-label="Extracted document details" className="mt-6 space-y-4">
      <h3 className="text-base font-semibold text-slate-800">Extracted details and verification checks</h3>
      {Object.entries(report.documents).map(([slot, result]) => <article key={slot} className="rounded-lg border border-slate-200 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h4 className="font-semibold text-slate-800">{result.documentType.replaceAll('_', ' ')}</h4>
          <span className={`rounded px-2 py-1 text-xs font-semibold ${result.status === 'VERIFIED' ? 'bg-green-100 text-green-800' : result.status === 'REJECTED' || result.status === 'FAILED' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-900'}`}>{result.status.replaceAll('_', ' ')}</span>
        </div>
        <dl className="mt-3 grid gap-2 sm:grid-cols-2">
          {Object.entries(result.extractedInformation).map(([key, value]) => <div key={key} className="rounded bg-slate-50 p-2">
            <dt className="text-xs font-medium capitalize text-slate-500">{key.replaceAll('_', ' ')}</dt>
            <dd className="break-words text-sm text-slate-800">{value === null || value === undefined || value === '' ? 'Not extracted' : typeof value === 'object' ? JSON.stringify(value) : String(value)}</dd>
          </div>)}
        </dl>
        <ul className="mt-3 space-y-1">
          {result.checks.map((item, index) => <li key={`${item.name}-${index}`} className={`text-xs ${item.status === 'PASS' ? 'text-green-800' : item.status === 'FAIL' ? 'text-red-700' : 'text-amber-800'}`}><strong>{item.status}:</strong> {item.reason}</li>)}
        </ul>
      </article>)}
      {report.checks.filter(item => item.slot === 'cross_document').length > 0 && <div className="rounded-lg border border-sky-200 bg-sky-50 p-4">
        <h4 className="font-semibold text-slate-800">Cross-document checks</h4>
        <ul className="mt-2 space-y-1">{report.checks.filter(item => item.slot === 'cross_document').map((item, index) => <li key={`${item.name}-${index}`} className={`text-xs ${item.status === 'PASS' ? 'text-green-800' : item.status === 'FAIL' ? 'text-red-700' : 'text-amber-800'}`}><strong>{item.status}:</strong> {item.reason}</li>)}</ul>
      </div>}
    </section>}
  </section>;
}
