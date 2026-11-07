import { ArrowRight, Check, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { money } from "../api";
import type { Garment, Project } from "../types";

interface Props {
  project: Project;
  busy: boolean;
  onSearch: (garments: Garment[], budget: number) => void;
}
export function ShoppingList({ project, busy, onSearch }: Props) {
  const [garments, setGarments] = useState(project.garments);
  const [budget, setBudget] = useState(project.budget);
  function edit(id: string, change: Partial<Garment>) {
    setGarments((items) =>
      items.map((item) => (item.id === id ? { ...item, ...change } : item)),
    );
  }
  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">From inspiration to the real thing</p>
          <h1>Your wardrobe, piece by piece.</h1>
          <p>
            A considered shopping list from your saved looks. Make it yours
            before we search.
          </p>
        </div>
      </div>
      <div className="list-summary">
        <span>
          <Check size={17} /> {project.selected.length} looks, {garments.length}{" "}
          pieces. Shared pieces count once.
        </span>
        <label>
          Total budget{" "}
          <div className="currency-input">
            <span>€</span>
            <input
              aria-label="Total shopping list budget"
              type="number"
              min="20"
              max="10000"
              value={budget}
              onChange={(event) => setBudget(Number(event.target.value))}
            />
          </div>
        </label>
      </div>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSearch(garments, budget);
        }}
      >
        <div className="shopping-table">
          <div className="shopping-table-head">
            <span>The piece / search keywords</span>
            <span>Your size</span>
            <span>Item budget</span>
            <span />
          </div>
          {garments.map((item, index) => (
            <div className="shopping-row" key={item.id}>
              <div className="garment-name">
                <span className="item-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <label>
                  <span className="category-label">{item.category}</span>
                  <input
                    aria-label={`Search keywords for ${item.name}`}
                    required
                    maxLength={120}
                    value={item.keywords}
                    onChange={(event) =>
                      edit(item.id, {
                        keywords: event.target.value,
                        name: event.target.value,
                      })
                    }
                  />
                </label>
              </div>
              <input
                aria-label={`Size for ${item.name}`}
                required
                maxLength={30}
                value={item.size}
                onChange={(event) =>
                  edit(item.id, { size: event.target.value })
                }
              />
              <div className="currency-input">
                <span>€</span>
                <input
                  aria-label={`Budget for ${item.name}`}
                  type="number"
                  min="1"
                  max="10000"
                  step="0.01"
                  required
                  value={item.budget}
                  onChange={(event) =>
                    edit(item.id, { budget: Number(event.target.value) })
                  }
                />
              </div>
              <button
                type="button"
                className="icon-button"
                aria-label={`Remove ${item.name}`}
                onClick={() =>
                  setGarments((items) =>
                    items.filter((piece) => piece.id !== item.id),
                  )
                }
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
        {!garments.length && (
          <p className="empty-state">
            All pieces removed. Go back to your sizes to rebuild the list.
          </p>
        )}
        <div className="search-explainer">
          <Search size={22} />
          <div>
            <h3>Good finds, with the details that matter.</h3>
            <p>
              We’ll compare matching listings from your connected marketplaces.
              Sizes, condition, and known shipping costs help us rank the
              candidates.
            </p>
          </div>
        </div>
        <div className="selection-bar">
          <div>
            <span>
              <strong>
                {garments.length} pieces · {money(budget)} total budget
              </strong>
              <small>
                Buying happens on the marketplace. You’re always in control.
              </small>
            </span>
          </div>
          <button
            className="button primary"
            disabled={busy || !garments.length}
          >
            Find my deals <ArrowRight size={17} />
          </button>
        </div>
      </form>
    </section>
  );
}
