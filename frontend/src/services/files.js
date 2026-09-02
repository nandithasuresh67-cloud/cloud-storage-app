import api from "./api";

export async function getFile(fileId) {
  const { data } = await api.get(`/files/${fileId}`);
  return data;
}
