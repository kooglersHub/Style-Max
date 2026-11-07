import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import App from "../App";
import { api } from "../api";
import { BriefForm } from "../components/BriefForm";

afterEach(() => vi.unstubAllGlobals());

it("opens the demo without transmitting personal photo files", async () => {
  const start = vi.fn();
  render(<BriefForm busy={false} config={null} onStart={start} />);
  await userEvent.click(
    screen.getByRole("button", { name: "Try the demo lookbook" }),
  );
  expect(start).toHaveBeenCalledWith(expect.any(String), 180, [], true);
});

it("requires three photos for personal generation and keeps the form editable", async () => {
  const start = vi.fn();
  render(<BriefForm busy={false} config={null} onStart={start} />);
  await userEvent.click(screen.getByRole("button", { name: /Quiet luxury/ }));
  await userEvent.click(
    screen.getByRole("button", { name: "Create my 10 looks" }),
  );
  expect(screen.getByRole("alert")).toHaveTextContent("Add three photos");
  expect(start).not.toHaveBeenCalled();
  expect(screen.getByLabelText("Describe your vibe")).toHaveValue(
    "Quiet luxury",
  );
});

it("shows an actionable error when the backend is unavailable", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockRejectedValue(new TypeError("network unavailable")),
  );
  vi.stubGlobal("scrollTo", vi.fn());
  render(<App />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Start the Style-Max backend",
  );
  expect(
    screen.getByRole("button", { name: "Try the demo lookbook" }),
  ).toBeEnabled();
});

it("preserves the provider setup error instead of showing fabricated results", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({ detail: "Connect the image worker first" }),
          { status: 503, headers: { "Content-Type": "application/json" } },
        ),
      ),
  );
  await expect(api("/projects/abc/generate", "POST")).rejects.toThrow(
    "Connect the image worker first",
  );
});
