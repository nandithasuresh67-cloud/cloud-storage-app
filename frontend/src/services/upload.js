import axios from "axios";
import api from "./api";

export async function initUpload({ filename, mimeType, sizeBytes, folderId }) {
  const { data } = await api.post("/files/init-upload", {
    filename,
    mime_type: mimeType,
    size_bytes: sizeBytes,
    folder_id: folderId || undefined,
  });
  return data;
}

/**
 * PUTs the raw file bytes straight to Supabase Storage's signed URL - a
 * plain axios call (not the `api` instance), since the destination is a
 * different origin entirely and must NOT send our auth cookies or go
 * through our baseURL.
 *
 * Supabase Storage sits behind an API gateway that requires an `apikey`
 * header on EVERY request, including this one - the `token` in the
 * signed URL's query string only authorizes writing to that specific
 * object, it does not satisfy the gateway's own project-level auth
 * check. Without this header the gateway rejects the request before it
 * ever reaches storage, which looks like a generic "upload failed" with
 * no useful detail. The anon/public key is safe to expose in frontend
 * code - that's its intended purpose, unlike the service_role key the
 * backend uses (which must never reach the browser).
 */
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

export function uploadBytes(uploadUrl, file, onProgress) {
  const headers = { "Content-Type": file.type || "application/octet-stream" };
  if (SUPABASE_ANON_KEY) {
    headers.apikey = SUPABASE_ANON_KEY;
    headers.Authorization = `Bearer ${SUPABASE_ANON_KEY}`;
  }
  return axios.put(uploadUrl, file, {
    headers,
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
}

export async function completeUpload(fileId) {
  const { data } = await api.post(`/files/${fileId}/complete-upload`, {});
  return data;
}
