import {
  ArrowRight,
  Check,
  ExternalLink,
  Package,
  RefreshCw,
  Search,
  ShoppingBag,
} from "lucide-react";
import { useState } from "react";
import { money, sourceName } from "../api";
import type { Project } from "../types";

interface Props {
  project: Project;
  busy: boolean;
  chosen: string[];
  onChoose: (id: string) => void;
  onSearch: () => void;
  onPreview: () => void;
}
export function Offers({
  project,
  busy,
  chosen,
  onChoose,
  onSearch,
  onPreview,
}: Props) {
  const [source, setSource] = useState("all");
  const [garment, setGarment] = useState("all");
  const offers = project.offers.filter(
    (item) =>
      (source === "all" || item.source === source) &&
      (garment === "all" || item.garment_id === garment),
  );
  const selected = project.offers.filter((item) => chosen.includes(item.id));
  const knownTotal = selected.reduce(
    (sum, item) => sum + (item.total ?? item.price),
    0,
  );
  const unknownShipping = selected.some((item) => item.shipping === null);
  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">The secondhand search</p>
          <h1>Good style. Better finds.</h1>
          <p>Pieces for your direction, with a second life ahead of them.</p>
        </div>
        <button
          className="button secondary small-button"
          disabled={busy}
          onClick={onSearch}
        >
          <RefreshCw size={15} /> Search again
        </button>
      </div>
      <div className="source-statuses">
        {project.sources.map((item) => (
          <div key={item.source} className="source-status">
            <span className={`status-dot ${item.status}`} />
            <strong>{sourceName(item.source)}</strong>
            <span>
              {item.status === "connected"
                ? "Connected"
                : item.status === "demo"
                  ? "Demo · search links"
                  : item.status === "error"
                    ? "Unavailable"
                    : item.status === "partial"
                      ? "Partial results"
                      : "Search links only"}
            </span>
          </div>
        ))}
      </div>
      {project.demo && (
        <div className="quiet-notice">
          <span className="demo-dot" />
          Demo mode never invents offers or prices. These links open real
          marketplace searches for your pieces.
        </div>
      )}
      <div className="offers-toolbar">
        <div className="tabs">
          {["all", "ebay", "vinted", "kleinanzeigen"].map((value) => (
            <button
              key={value}
              className={source === value ? "active" : ""}
              onClick={() => setSource(value)}
            >
              {value === "all" ? "All marketplaces" : sourceName(value)}
            </button>
          ))}
        </div>
        <label className="sr-only" htmlFor="garment-filter">
          Filter by garment
        </label>
        <select
          id="garment-filter"
          value={garment}
          onChange={(event) => setGarment(event.target.value)}
        >
          <option value="all">All pieces</option>
          {project.garments.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
      </div>
      {offers.length > 0 ? (
        <div className="offer-grid">
          {offers.map((item) => (
            <article
              className={`offer-card ${chosen.includes(item.id) ? "chosen" : ""}`}
              key={item.id}
            >
              <div className="offer-image">
                {item.image && /^https:\/\//.test(item.image) ? (
                  <img
                    referrerPolicy="no-referrer"
                    src={item.image}
                    alt={item.title}
                    loading="lazy"
                    onError={(event) => {
                      event.currentTarget.style.display = "none";
                    }}
                  />
                ) : (
                  <Package size={45} strokeWidth={1} />
                )}
                <span className="market-tag">{sourceName(item.source)}</span>
                <button
                  className={`save-look ${chosen.includes(item.id) ? "saved" : ""}`}
                  aria-label={`${chosen.includes(item.id) ? "Remove" : "Choose"} ${item.title}`}
                  aria-pressed={chosen.includes(item.id)}
                  onClick={() => onChoose(item.id)}
                >
                  <Check size={18} />
                </button>
              </div>
              <div className="offer-details">
                <div className="offer-price">
                  <strong>{money(item.price)}</strong>
                  <span>
                    {item.shipping === null
                      ? "+ shipping unknown"
                      : `+ ${money(item.shipping)} shipping`}
                  </span>
                </div>
                <h3>{item.title}</h3>
                <p className="offer-meta">
                  {item.size || "Size to confirm"} <span>·</span>{" "}
                  {item.condition}
                </p>
                <div className="offer-reasons">
                  {item.reasons.slice(0, 3).map((reason) => (
                    <span key={reason}>
                      <Check size={11} />
                      {reason}
                    </span>
                  ))}
                </div>
                <a
                  className="listing-link"
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View listing <ExternalLink size={13} />
                </a>
              </div>
            </article>
          ))}
        </div>
      ) : (
        !project.demo && (
          <div className="empty-state">
            <Search size={28} />
            <h3>No live matches in this search.</h3>
            <p>
              Try broader keywords, check your source connections, or explore
              the searches below.
            </p>
          </div>
        )
      )}
      <div className="search-links-heading">
        <div>
          <h2>Take a look around.</h2>
          <p>
            Search each piece directly. Availability, sizes and prices are
            confirmed on the marketplace.
          </p>
        </div>
        <span className="small muted">Search links · not verified offers</span>
      </div>
      <div className="search-link-list">
        {project.garments
          .filter((item) => garment === "all" || item.id === garment)
          .map((item, index) => (
            <div className="search-link-row" key={item.id}>
              <span className="item-number">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <h3>{item.name}</h3>
                <p>
                  Size {item.size} <span>·</span> Target {money(item.budget)}
                </p>
              </div>
              <div className="market-links">
                {project.search_links
                  .filter(
                    (link) =>
                      link.garment_id === item.id &&
                      (source === "all" || link.source === source),
                  )
                  .map((link) => (
                    <a
                      key={link.source}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={`Search ${sourceName(link.source)} for ${item.name}`}
                    >
                      {sourceName(link.source)} <ExternalLink size={12} />
                    </a>
                  ))}
              </div>
            </div>
          ))}
      </div>
      <div className="selection-bar">
        <div>
          <ShoppingBag size={21} />
          <span>
            <strong>
              {project.demo
                ? "Explore your final outfit"
                : `${chosen.length} pieces selected · ${money(knownTotal)}${unknownShipping ? " + unknown shipping" : ""}`}
            </strong>
            <small>
              {knownTotal > project.budget
                ? "Your selection is above your total budget."
                : "Outfit previews are visual ideas. Check measurements before buying."}
            </small>
          </span>
        </div>
        <button
          className="button primary"
          disabled={busy || (!project.demo && !chosen.length)}
          onClick={onPreview}
        >
          See the outfit <ArrowRight size={17} />
        </button>
      </div>
    </section>
  );
}
