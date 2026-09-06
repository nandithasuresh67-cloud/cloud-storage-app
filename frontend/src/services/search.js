import api from "./api";

export async function search({ q, itemType, mimeType }) {
  const { data } = await api.get("/search", {
    params: {
      q,
      ...(itemType ? { item_type: itemType } : {}),
      ...(mimeType ? { mime_type: mimeType } : {}),
    },
  });
  return data;
}
