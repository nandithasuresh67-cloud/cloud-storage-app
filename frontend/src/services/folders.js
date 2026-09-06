import api from "./api";

export async function getFolderContents(folderId, { sortBy = "name", sortOrder = "asc", limit = 25, offset = 0 } = {}) {
  const { data } = await api.get("/folders/contents", {
    params: {
      ...(folderId ? { folder_id: folderId } : {}),
      sort_by: sortBy,
      sort_order: sortOrder,
      limit,
      offset,
    },
  });
  return data;
}

export async function createFolder({ name, parentId }) {
  const { data } = await api.post("/folders", { name, parent_id: parentId || undefined });
  return data;
}

export async function deleteFolder(folderId) {
  await api.delete(`/folders/${folderId}`);
}
