export interface Garment {
  fit?: "relaxed" | "regular" | "slim";
  audience?: "menswear" | "womenswear" | "all";
  id: string;
  name: string;
  category: "tops" | "outerwear" | "bottoms" | "shoes" | "accessories";
  color: string;
  keywords: string;
  size: string;
  budget: number;
  look_ids: string[];
}
export interface Look {
  id: string;
  title: string;
  description: string;
  prompt: string;
  palette: string[];
  garments: Garment[];
  status: "queued" | "running" | "completed" | "failed";
  image: string | null;
  error: string | null;
}
export interface Sizes {
  tops: string;
  outerwear: string;
  bottoms: string;
  shoes: string;
  fit: "relaxed" | "regular" | "slim";
  category: "menswear" | "womenswear" | "all";
}
export interface Offer {
  id: string;
  garment_id: string;
  source: string;
  external_id: string;
  url: string;
  title: string;
  price: number;
  shipping: number | null;
  total: number | null;
  image: string | null;
  size: string | null;
  size_status: string;
  condition: string;
  score: number;
  reasons: string[];
}
export interface Project {
  id: string;
  vibe: string;
  budget: number;
  demo: boolean;
  created_at: string;
  updated_at: string;
  photos: string[];
  looks: Look[];
  selected: string[];
  sizes: Sizes | null;
  garments: Garment[];
  offers: Offer[];
  search_links: {
    garment_id: string;
    source: string;
    url: string;
    kind: string;
  }[];
  sources: { source: string; status: string; message: string }[];
  basket?: {
    offer_ids: string[];
    known_total: number;
    complete: boolean;
    unmatched: string[];
    sizes_confirmed: boolean;
  };
  job: {
    id: string;
    kind: string;
    status: string;
    completed: number;
    total: number;
  } | null;
  error: string | null;
  preview: {
    demo: boolean;
    image: string | null;
    offer_ids: string[];
    missing_images: string[];
  } | null;
}
export interface Config {
  image_worker_configured: boolean;
  planner: string;
  photo_destination: string;
  sources: Record<string, boolean>;
}
export type Stage = "brief" | "looks" | "fit" | "list" | "offers" | "preview";
