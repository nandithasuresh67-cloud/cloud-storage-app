import { File, FileArchive, FileText, Image, Music, Video } from "lucide-react";

export default function FileTypeIcon({ mimeType, className }) {
  if (!mimeType) return <File className={className} strokeWidth={1.75} />;
  if (mimeType.startsWith("image/")) return <Image className={className} strokeWidth={1.75} />;
  if (mimeType.startsWith("video/")) return <Video className={className} strokeWidth={1.75} />;
  if (mimeType.startsWith("audio/")) return <Music className={className} strokeWidth={1.75} />;
  if (mimeType === "application/pdf" || mimeType.startsWith("text/")) {
    return <FileText className={className} strokeWidth={1.75} />;
  }
  if (mimeType.includes("zip") || mimeType.includes("compressed")) {
    return <FileArchive className={className} strokeWidth={1.75} />;
  }
  return <File className={className} strokeWidth={1.75} />;
}
