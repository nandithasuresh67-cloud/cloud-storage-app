import api from "./api";

export async function getFolderContents(folderId) {
  const { data } = await api.get("/folders/contents", {
    params: folderId ? { folder_id: folderId } : {},
  });
  return data;
}

export async function createFolder({ name, parentId }) {
  const { data } = await api.post("/folders", { name, parent_id: parentId || undefined });
  return data;
}
