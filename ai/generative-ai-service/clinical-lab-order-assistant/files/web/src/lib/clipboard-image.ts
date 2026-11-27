/** Read only the image explicitly supplied by a paste event (no clipboard permissions). */
export function clipboardImages(data: Pick<DataTransfer, "items" | "files">): File[] {
  const items = Array.from(data.items).filter(item => item.kind === "file" && item.type.startsWith("image/"));
  const images = items.length
    ? items.map(item => item.getAsFile()).filter((file): file is File => file !== null)
    : Array.from(data.files).filter(file => file.type.startsWith("image/"));
  return images.map((file, index) => {
  const extension = ({ "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp" } as Record<string, string>)[file.type];
  if (!extension) throw new Error("Paste a PNG, JPEG or WebP image.");
  // Clipboard filenames are often missing or do not match their MIME type.
  return new File([file], `Pasted image ${new Date().toLocaleTimeString("en-GB").replaceAll(":", "-")}${images.length > 1 ? ` (${index+1})` : ""}.${extension}`, { type: file.type });
  });
}
