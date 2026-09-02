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
 */
export function uploadBytes(uploadUrl, file, onProgress) {
  return axios.put(uploadUrl, file, {
    headers: { "Content-Type": file.type || "application/octet-stream" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
}

export async function completeUpload(fileId) {
  const { data } = await api.post(`/files/${fileId}/complete-upload`, {});
  return data;
}
