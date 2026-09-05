import api from "./api";

function targetParams(fileId, folderId) {
  return fileId ? { file_id: fileId } : { folder_id: folderId };
}

export async function listPublicLinks({ fileId, folderId }) {
  const { data } = await api.get("/public-link", { params: targetParams(fileId, folderId) });
  return data;
}

export async function createPublicLink({ fileId, folderId, expiresInHours, password }) {
  const { data } = await api.post("/public-link", {
    file_id: fileId || undefined,
    folder_id: folderId || undefined,
    expires_in_hours: expiresInHours || undefined,
    password: password || undefined,
  });
  return data;
}

export async function revokePublicLink(linkId) {
  await api.delete(`/public-link/${linkId}`);
}

export async function accessPublicLink(token, password) {
  const { data } = await api.post(`/public-link/${token}/access`, password ? { password } : {});
  return data;
}
