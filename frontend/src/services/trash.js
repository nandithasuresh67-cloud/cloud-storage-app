import api from "./api";

export async function getTrash() {
  const { data } = await api.get("/trash");
  return data;
}

export async function restoreTrashItem(type, id) {
  const resource = type === "folder" ? "folders" : "files";
  await api.post(`/trash/${resource}/${id}/restore`);
}

export async function permanentlyDeleteTrashItem(type, id) {
  const resource = type === "folder" ? "folders" : "files";
  await api.delete(`/trash/${resource}/${id}`);
}
