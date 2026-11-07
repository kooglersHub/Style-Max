import {
  ArrowRight,
  Check,
  Heart,
  RotateCcw,
  SlidersHorizontal,
} from "lucide-react";
import { useState } from "react";
import type { Project } from "../types";
import { FashionFigure } from "./FashionFigure";

interface Props {
  project: Project;
  onToggle: (id: string) => void;
  onContinue: () => void;
  onRetry: () => void;
  busy: boolean;
}
export function LookGallery({
  project,
  onToggle,
  onContinue,
  onRetry,
  busy,
}: Props) {
  const [savedOnly, setSavedOnly] = useState(false);
  const looks = project.looks.filter(
    (look) => !savedOnly || project.selected.includes(look.id),
  );
  return (
    <section className="gallery-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Your personal lookbook</p>
          <h1>Same you. New possibilities.</h1>
          <p>
            Save the looks that feel like you. We’ll find the pieces to make
            them happen.
          </p>
        </div>
        <span className="edition">01—10 / Style studies</span>
      </div>
      {project.demo && (
        <div className="quiet-notice">
          <span className="demo-dot" />
          Demo lookbook · These illustrations are style examples, not generated
          photos of you.
        </div>
      )}
      <div className="gallery-toolbar">
        <div className="tabs">
          <button
            className={!savedOnly ? "active" : ""}
            onClick={() => setSavedOnly(false)}
          >
            All looks <span>{project.looks.length}</span>
          </button>
          <button
            className={savedOnly ? "active" : ""}
            onClick={() => setSavedOnly(true)}
          >
            Saved <span>{project.selected.length}</span>
          </button>
        </div>
        <span className="muted small">
          <SlidersHorizontal size={14} /> Made for your direction
        </span>
      </div>
      {!looks.length && (
        <div className="empty-state">
          <Heart size={28} />
          <h3>
            {savedOnly
              ? "Your favorites live here."
              : "Your looks are on their way."}
          </h3>
          <p>
            {savedOnly
              ? "Tap a heart on any look to save it."
              : "Your AI stylist is putting together ten different directions."}
          </p>
        </div>
      )}
      <div className="look-grid">
        {looks.map((look, index) => {
          const selected = project.selected.includes(look.id);
          return (
            <article
              className={`look-card ${selected ? "selected" : ""}`}
              key={look.id}
            >
              <div className="look-image">
                {look.image ? (
                  <img src={look.image} alt={look.title} loading="lazy" />
                ) : project.demo ? (
                  <FashionFigure
                    palette={look.palette}
                    variant={project.looks.indexOf(look)}
                    title={`${look.title} — demo illustration`}
                  />
                ) : (
                  <div className={`image-pending ${look.status}`}>
                    <span className="mini-spinner" />
                    <p>
                      {look.status === "failed"
                        ? "Couldn’t generate this look"
                        : "Creating your look"}
                    </p>
                    <span>
                      {look.error ||
                        "A little patience. Good things take time."}
                    </span>
                  </div>
                )}
                <span className="look-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <button
                  className={`save-look ${selected ? "saved" : ""}`}
                  aria-label={`${selected ? "Unsave" : "Save"} ${look.title}`}
                  aria-pressed={selected}
                  disabled={look.status !== "completed" || busy}
                  onClick={() => onToggle(look.id)}
                >
                  <Heart size={18} fill={selected ? "currentColor" : "none"} />
                </button>
                {selected && (
                  <span className="selected-tag">
                    <Check size={12} /> In your edit
                  </span>
                )}
              </div>
              <div className="look-caption">
                <h3>{look.title}</h3>
                <div className="palette" aria-label="Color palette">
                  {look.palette.map((color, i) => (
                    <span
                      key={i}
                      style={{
                        backgroundColor: /^#[\da-f]{3,8}$/i.test(color)
                          ? color
                          : "#888",
                      }}
                    />
                  ))}
                </div>
              </div>
              <p className="look-description">{look.description}</p>
            </article>
          );
        })}
      </div>
      {project.error && (
        <div className="inline-error">
          <p>{project.error}</p>
          <button className="text-button" onClick={onRetry} disabled={busy}>
            <RotateCcw size={15} /> Retry unfinished looks
          </button>
        </div>
      )}
      <div className="selection-bar">
        <div>
          <Heart size={20} />
          <span>
            <strong>
              {project.selected.length}{" "}
              {project.selected.length === 1 ? "look" : "looks"} saved
            </strong>
            <small>A good wardrobe starts with a few favorites.</small>
          </span>
        </div>
        <button
          className="button primary"
          disabled={!project.selected.length || busy}
          onClick={onContinue}
        >
          Find my pieces <ArrowRight size={17} />
        </button>
      </div>
    </section>
  );
}
