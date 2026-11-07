import { ArrowRight, Ruler } from "lucide-react";
import { useState } from "react";
import type { Project, Sizes } from "../types";
import { FashionFigure } from "./FashionFigure";

interface Props {
  project: Project;
  busy: boolean;
  onSubmit: (sizes: Sizes) => void;
}
const letters = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"];
export function FitForm({ project, busy, onSubmit }: Props) {
  const [sizes, setSizes] = useState<Sizes>(
    project.sizes || {
      tops: "",
      outerwear: "",
      bottoms: "",
      shoes: "",
      fit: "relaxed",
      category: "all",
    },
  );
  const look = project.looks.find((look) => project.selected.includes(look.id));
  function set<K extends keyof Sizes>(key: K, value: Sizes[K]) {
    setSizes((previous) => ({ ...previous, [key]: value }));
  }
  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">The right fit</p>
          <h1>Let’s make it your size.</h1>
          <p>
            A great look should feel as good as it looks. Tell us what you
            usually wear.
          </p>
        </div>
      </div>
      <div className="fit-layout">
        <form
          className="fit-form paper-panel"
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit(sizes);
          }}
        >
          <div className="panel-heading">
            <Ruler size={20} />
            <h2>Your size profile</h2>
          </div>
          <p className="muted">
            Use the sizes on your favorite clothes. You can refine each piece
            next.
          </p>
          <div className="field-grid">
            {(["tops", "outerwear"] as const).map((key) => (
              <label key={key}>
                {key === "tops" ? "Tops" : "Outerwear"}
                <select
                  required
                  value={sizes[key]}
                  onChange={(event) => set(key, event.target.value)}
                >
                  <option value="">Select size</option>
                  {letters.map((size) => (
                    <option key={size}>{size}</option>
                  ))}
                </select>
              </label>
            ))}
            <label>
              Trousers
              <input
                required
                maxLength={30}
                placeholder="e.g. W32 L32 or EU 40"
                value={sizes.bottoms}
                onChange={(event) => set("bottoms", event.target.value)}
              />
            </label>
            <label>
              Shoes · EU
              <select
                required
                value={sizes.shoes}
                onChange={(event) => set("shoes", event.target.value)}
              >
                <option value="">Select size</option>
                {Array.from({ length: 19 }, (_, i) => String(32 + i)).map(
                  (size) => (
                    <option key={size}>{size}</option>
                  ),
                )}
              </select>
            </label>
          </div>
          <label>
            Shopping category
            <select
              value={sizes.category}
              onChange={(event) =>
                set("category", event.target.value as Sizes["category"])
              }
            >
              <option value="all">All clothing</option>
              <option value="menswear">Menswear</option>
              <option value="womenswear">Womenswear</option>
            </select>
          </label>
          <fieldset>
            <legend>How do you like your clothes to fit?</legend>
            <div className="segmented">
              {(["relaxed", "regular", "slim"] as const).map((fit) => (
                <button
                  key={fit}
                  type="button"
                  aria-pressed={sizes.fit === fit}
                  className={sizes.fit === fit ? "active" : ""}
                  onClick={() => set("fit", fit)}
                >
                  {fit}
                </button>
              ))}
            </div>
          </fieldset>
          <p className="small muted">
            Sizes come from you, never from your photos. Brand sizing varies, so
            check seller measurements before buying.
          </p>
          <button className="button primary full" disabled={busy}>
            Build my shopping list <ArrowRight size={17} />
          </button>
        </form>
        <aside className="fit-aside">
          <div className="fit-illustration">
            {look?.image ? (
              <img src={look.image} alt={look.title} />
            ) : (
              <FashionFigure palette={look?.palette} variant={1} />
            )}
          </div>
          <p className="serif">
            “The best thing you can wear
            <br />
            is something that feels like you.”
          </p>
          <span className="small muted">
            {project.selected.length} saved{" "}
            {project.selected.length === 1 ? "direction" : "directions"} · One
            considered wardrobe
          </span>
        </aside>
      </div>
    </section>
  );
}
