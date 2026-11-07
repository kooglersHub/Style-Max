import {
  ArrowRight,
  Check,
  ImagePlus,
  Leaf,
  LockKeyhole,
  Play,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { Config } from "../types";
import { FashionFigure } from "./FashionFigure";
import { money } from "../api";

interface Props {
  busy: boolean;
  config: Config | null;
  onStart: (
    vibe: string,
    budget: number,
    photos: File[],
    demo: boolean,
  ) => void;
}
const presets = [
  "Quiet luxury",
  "Everyday minimal",
  "Vintage & relaxed",
  "Scandi layers",
  "Streetwear",
  "Something new",
];
export function BriefForm({ busy, config, onStart }: Props) {
  const [vibe, setVibe] = useState("");
  const [budget, setBudget] = useState(180);
  const [files, setFiles] = useState<File[]>([]);
  const [urls, setUrls] = useState<string[]>([]);
  const [error, setError] = useState("");
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const previews = files.map((file) => URL.createObjectURL(file));
    setUrls(previews);
    return () => previews.forEach((url) => URL.revokeObjectURL(url));
  }, [files]);
  function addFiles(incoming: FileList | null) {
    if (!incoming) return;
    const next = [...files, ...Array.from(incoming)];
    if (next.length > 3)
      return setError(
        "Choose exactly three photos. Remove one before adding another.",
      );
    if (
      next.some(
        (file) =>
          file.size > 10 * 1024 * 1024 ||
          !["image/jpeg", "image/png", "image/webp"].includes(file.type),
      )
    )
      return setError("Use JPEG, PNG or WebP photos under 10 MB each.");
    setError("");
    setFiles(next);
  }
  return (
    <section className="brief-section">
      <div className="intro-layout">
        <div className="intro-copy">
          <span className="intro-kicker">
            <span /> A better wardrobe, a second life.
          </span>
          <h1>
            Your next look.
            <br />
            <span className="serif">Already out there.</span>
          </h1>
          <p>
            Find your style. See it on you. Discover the pieces
            <br className="desktop-break" /> pre-loved, well-priced, and
            unmistakably yours.
          </p>
          <div className="intro-proof">
            <span>
              <Check size={14} /> Styled around you
            </span>
            <span>
              <Leaf size={14} /> Secondhand first
            </span>
          </div>
        </div>
        <div
          className="hero-editorial"
          aria-label="Three illustrated outfit directions"
        >
          <span className="editorial-note">A few ways to be you.</span>
          <div className="editorial-print print-back">
            <FashionFigure
              palette={["#b5a188", "#eee5d5", "#575d52"]}
              variant={1}
            />
            <span>02 / A little more considered</span>
          </div>
          <div className="editorial-print print-front">
            <FashionFigure />
            <span>01 / Your everyday, reimagined</span>
          </div>
          <div className="editorial-stamp">
            <span>Good style.</span>
            <span>Better finds.</span>
            <ArrowRight size={18} />
          </div>
        </div>
      </div>
      <div className="brief-divider">
        <span>Let’s find your direction</span>
        <span>01 — Start with you</span>
      </div>
      <form
        className="brief-layout"
        onSubmit={(event) => {
          event.preventDefault();
          if (files.length !== 3)
            return setError(
              "Add three photos to create your personal looks, or explore the demo.",
            );
          onStart(vibe, budget, files, false);
        }}
      >
        <div className="brief-fields">
          <div className="form-section">
            <div className="numbered-heading">
              <span>01</span>
              <div>
                <h2>What’s your vibe?</h2>
                <p>
                  A feeling, a place, a whole new era. Tell us what you’re
                  after.
                </p>
              </div>
            </div>
            <label className="sr-only" htmlFor="vibe">
              Describe your vibe
            </label>
            <textarea
              id="vibe"
              required
              minLength={3}
              maxLength={1200}
              rows={4}
              placeholder="Think relaxed earth tones, a great overshirt, and the kind of outfit I’d wear to a Sunday coffee…"
              value={vibe}
              onChange={(event) => setVibe(event.target.value)}
            />
            <div className="vibe-chips">
              {presets.map((preset) => (
                <button
                  type="button"
                  key={preset}
                  className={vibe === preset ? "chosen" : ""}
                  onClick={() => setVibe(preset)}
                >
                  {preset}
                  <span>↗</span>
                </button>
              ))}
            </div>
          </div>
          <div className="form-section budget-section">
            <div className="numbered-heading">
              <span>02</span>
              <div>
                <h2>A budget that feels right.</h2>
                <p>
                  For your entire shopping list, across all your chosen looks.
                </p>
              </div>
            </div>
            <div className="budget-display">
              <span>Total wardrobe budget</span>
              <strong>{money(budget)}</strong>
            </div>
            <label className="sr-only" htmlFor="budget">
              Total shopping budget
            </label>
            <input
              id="budget"
              type="range"
              min="40"
              max="500"
              step="10"
              value={budget}
              onChange={(event) => setBudget(Number(event.target.value))}
            />
            <div className="range-labels">
              <span>€40 · A few good finds</span>
              <span>€500 · A fresh start</span>
            </div>
          </div>
        </div>
        <div className="photo-panel">
          <div className="numbered-heading">
            <span>03</span>
            <div>
              <h2>A little reference.</h2>
              <p>Three photos. So the looks look like you.</p>
            </div>
          </div>
          <input
            ref={input}
            type="file"
            className="sr-only"
            accept="image/jpeg,image/png,image/webp"
            multiple
            aria-label="Upload three reference photos"
            onChange={(event) => {
              addFiles(event.target.files);
              event.target.value = "";
            }}
          />
          <div
            className="photo-slots"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              addFiles(event.dataTransfer.files);
            }}
          >
            {[0, 1, 2].map((index) => (
              <div
                className={`photo-slot ${urls[index] ? "filled" : ""}`}
                key={index}
              >
                {urls[index] ? (
                  <>
                    <img
                      src={urls[index]}
                      alt={`Reference photo ${index + 1}`}
                    />
                    <button
                      type="button"
                      aria-label={`Remove reference photo ${index + 1}`}
                      onClick={() =>
                        setFiles(files.filter((_, i) => i !== index))
                      }
                    >
                      <X size={13} />
                    </button>
                    <span>
                      <Check size={12} />
                    </span>
                  </>
                ) : (
                  <button type="button" onClick={() => input.current?.click()}>
                    <ImagePlus size={23} strokeWidth={1.2} />
                    <span>
                      {["Full body", "Portrait", "Another angle"][index]}
                    </span>
                    <small>Add photo</small>
                  </button>
                )}
              </div>
            ))}
          </div>
          <p className="photo-tip">
            Natural light. Just you. A full-length photo helps us get the
            proportions right.
          </p>
          <div className="privacy-note">
            <LockKeyhole size={15} />
            <p>
              Your photos stay in your private studio and are sent to your
              configured AI service only when you generate. Delete your project
              to remove them.
            </p>
          </div>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          {!config?.image_worker_configured && (
            <p className="setup-hint">
              Personal generation needs a connected image worker. You can
              explore the complete demo now.
            </p>
          )}
          <button className="button primary full" disabled={busy}>
            Create my 10 looks <ArrowRight size={17} />
          </button>
          <button
            type="button"
            className="button demo-button full"
            disabled={busy}
            onClick={() =>
              onStart(
                vibe ||
                  "Relaxed earth tones, thoughtful layers, everyday essentials",
                budget,
                [],
                true,
              )
            }
          >
            <Play size={14} /> Try the demo lookbook <ArrowRight size={15} />
          </button>
          <span className="small muted centered">
            No photos needed for the demo.
          </span>
        </div>
      </form>
      <div className="marketplace-footer">
        <span>Great pieces deserve another chapter.</span>
        <div>
          <strong className="vinted-wordmark">Vinted</strong>
          <strong className="ebay-wordmark">ebay</strong>
          <strong className="klein-wordmark">kleinanzeigen</strong>
          <span className="small">Independent studio · Not affiliated</span>
        </div>
      </div>
    </section>
  );
}
