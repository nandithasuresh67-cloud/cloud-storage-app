import { useCallback, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { completeUpload, initUpload, uploadBytes } from "../services/upload";

/**
 * Manages a client-side queue of in-flight uploads for the current
 * folder. Each entry tracks its own progress/status so multiple files
 * can upload concurrently and independently - one failing (oversized,
 * blocked type, network blip) doesn't affect the others.
 */
export function useFileUpload(folderId) {
  const [uploads, setUploads] = useState([]); // [{ clientId, name, progress, status, error }]
  const queryClient = useQueryClient();
  const nextId = useRef(0);

  const updateUpload = useCallback((clientId, patch) => {
    setUploads((prev) => prev.map((u) => (u.clientId === clientId ? { ...u, ...patch } : u)));
  }, []);

  const dismissUpload = useCallback((clientId) => {
    setUploads((prev) => prev.filter((u) => u.clientId !== clientId));
  }, []);

  const uploadOne = useCallback(
    async (file, clientId) => {
      try {
        updateUpload(clientId, { status: "starting", progress: 0 });
        const initResponse = await initUpload({
          filename: file.name,
          mimeType: file.type || "application/octet-stream",
          sizeBytes: file.size,
          folderId,
        });

        updateUpload(clientId, { status: "uploading" });
        await uploadBytes(initResponse.upload_url, file, (progress) => updateUpload(clientId, { progress }));

        updateUpload(clientId, { status: "finishing", progress: 100 });
        await completeUpload(initResponse.file_id);

        updateUpload(clientId, { status: "done" });
        queryClient.invalidateQueries({ queryKey: ["folder-contents", folderId || "root"] });
      } catch (err) {
        const message = err?.response?.data?.detail || "Upload failed. Please try again.";
        updateUpload(clientId, { status: "error", error: message });
      }
    },
    [folderId, queryClient, updateUpload]
  );

  const startUpload = useCallback(
    (files) => {
      const newEntries = Array.from(files).map((file) => ({
        clientId: nextId.current++,
        file,
        name: file.name,
        progress: 0,
        status: "queued",
        error: null,
      }));
      setUploads((prev) => [...prev, ...newEntries]);
      newEntries.forEach((entry) => uploadOne(entry.file, entry.clientId));
    },
    [uploadOne]
  );

  return { uploads, startUpload, dismissUpload };
}
