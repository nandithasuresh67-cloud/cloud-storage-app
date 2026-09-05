import api from "./api";

function targetParams(fileId, folderId) {
  return fileId ? { file_id: fileId } : { folder_id: folderId };
}

export async function listShares({ fileId, folderId }) {
  const { data } = await api.get("/shares", { params: targetParams(fileId, folderId) });
  return data;
}

export async function createShare({ fileId, folderId, email, role }) {
  const { data } = await api.post("/shares", {
    file_id: fileId || undefined,
    folder_id: folderId || undefined,
    email,
    role,
  });
  return data;
}

export async function revokeShare(shareId) {
  await api.delete(`/shares/${shareId}`);
}

export async function getSharedWithMe() {
  const { data } = await api.get("/shares/shared-with-me");
  return data;
}
