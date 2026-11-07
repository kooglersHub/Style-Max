import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import App from "../App";
import type { Project } from "../types";

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

it("lets a completed-preview project return to its lookbook and change favorites", async () => {
  const project: Project = {
    id: "review-project",
    vibe: "Earth tones",
    budget: 180,
    demo: true,
    created_at: "2026-11-07",
    updated_at: "2026-11-07",
    photos: [],
    looks: ["The everyday edit", "Soft tailoring"].map((title, index) => ({
      id: `look-${index + 1}`,
      title,
      description: "Thoughtful layers in warm shades.",
      prompt: "Full outfit",
      palette: ["#888", "#eee", "#333"],
      garments: [],
      status: "completed",
      image: null,
      error: null,
    })),
    selected: ["look-1"],
    sizes: null,
    garments: [],
    offers: [],
    search_links: [],
    sources: [],
    job: {
      id: "finished-preview",
      kind: "preview",
      status: "completed",
      completed: 1,
      total: 1,
    },
    error: null,
    preview: { demo: true, image: null, offer_ids: [], missing_images: [] },
  };
  localStorage.setItem("stylemax_project", project.id);
  vi.stubGlobal("scrollTo", vi.fn());
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async (url: string) =>
        new Response(
          JSON.stringify(
            url.endsWith("/config")
              ? {
                  image_worker_configured: false,
                  planner: "local",
                  sources: {},
                }
              : [project],
          ),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
    ),
  );
  render(<App />);
  await screen.findByRole("heading", { name: "A look worth making yours." });
  await userEvent.click(
    screen.getByRole("button", { name: "The lookbook" }),
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Save Soft tailoring" }),
  );
  expect(
    screen.getByRole("heading", { name: "Same you. New possibilities." }),
  ).toBeVisible();
  expect(
    screen.getByRole("button", { name: "Unsave Soft tailoring" }),
  ).toBeVisible();
});
