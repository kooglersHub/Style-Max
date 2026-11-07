export class ApiError extends Error {}

export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const form = body instanceof FormData;
  const response = await fetch("/api" + path, {
    method,
    credentials: "same-origin",
    headers: body && !form ? { "Content-Type": "application/json" } : undefined,
    body: body ? (form ? body : JSON.stringify(body)) : undefined,
  });
  if (!response.ok) {
    let message = `Request failed (${response.status}). Please try again.`;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail))
        message = data.detail
          .map((item: { msg: string }) => item.msg)
          .join(". ");
    } catch {
      /* Preserve a readable message for non-JSON proxy failures. */
    }
    throw new ApiError(message);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

export const money = (value: number) =>
  new Intl.NumberFormat("en-DE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 2,
  }).format(value);
export const sourceName = (value: string) =>
  ({ ebay: "eBay", vinted: "Vinted", kleinanzeigen: "Kleinanzeigen" })[value] ||
  value;
