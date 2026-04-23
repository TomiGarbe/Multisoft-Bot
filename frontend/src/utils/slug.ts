export function generateSlug(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')     // remove special chars
    .replace(/\s+/g, '-')         // spaces → dash
    .replace(/-+/g, '-');         // collapse dashes
}