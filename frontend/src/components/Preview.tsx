import { ArrowLeft, ExternalLink, Leaf } from "lucide-react";
import { money, sourceName } from "../api";
import type { Project } from "../types";
import { FashionFigure } from "./FashionFigure";

export function Preview({
  project,
  onBack,
}: {
  project: Project;
  onBack: () => void;
}) {
  const look = project.looks.find((item) => project.selected.includes(item.id));
  const selected = project.offers.filter((item) =>
    project.preview?.offer_ids.includes(item.id),
  );
  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Your next chapter</p>
          <h1>A look worth making yours.</h1>
          <p>Inspired by you. Put together with a little more intention.</p>
        </div>
      </div>
      <div className="preview-layout">
        <div className="preview-image">
          {project.preview?.image ? (
            <img
              src={project.preview.image}
              alt="AI outfit visualization using your selected offers"
            />
          ) : (
            <FashionFigure
              palette={look?.palette}
              variant={project.looks.indexOf(look!)}
              title="Demo outfit illustration"
            />
          )}
          <span className="preview-caption">
            {project.demo
              ? "Demo illustration · not your likeness"
              : "AI visualization · fit and details may differ"}
          </span>
        </div>
        <div className="preview-notes">
          <span className="tag">
            <Leaf size={13} /> A second life. A fresh start.
          </span>
          <h2 className="serif">{look?.title || "Your own direction"}</h2>
          <p>{look?.description}</p>
          {project.demo ? (
            <div className="demo-preview-note">
              <h3>This is where your outfit comes together.</h3>
              <p>
                With the AI worker and marketplaces connected, you’ll see
                yourself wearing your selected finds, alongside the exact
                listing links.
              </p>
              <p>
                This demo uses an illustration. No offers or personal photos
                have been generated.
              </p>
            </div>
          ) : (
            <div className="selected-pieces">
              {selected.map((item) => (
                <a
                  key={item.id}
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <div>
                    <strong>{item.title}</strong>
                    <span>
                      {sourceName(item.source)} · {item.size || "Confirm size"}
                    </span>
                  </div>
                  <span>
                    {money(item.price)} <ExternalLink size={13} />
                  </span>
                </a>
              ))}
            </div>
          )}
          {project.preview?.missing_images.length ? (
            <p className="quiet-notice">
              Product images were unavailable for:{" "}
              {project.preview.missing_images.join(", ")}. These pieces were
              described in text.
            </p>
          ) : null}
          <p className="small muted">
            This is a styling visualization, not a fit guarantee. Check
            measurements, condition, shipping and availability on the original
            listing.
          </p>
          <button className="button secondary" onClick={onBack}>
            <ArrowLeft size={16} /> Back to the finds
          </button>
        </div>
      </div>
    </section>
  );
}
