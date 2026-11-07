import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { LookGallery } from "../components/LookGallery";
import { FitForm } from "../components/FitForm";
import type { Project } from "../types";

const project = {
  id: "abc",
  demo: true,
  selected: [],
  looks: [
    {
      id: "look-1",
      title: "Soft tailoring",
      description: "Relaxed neutral layers",
      palette: ["#777"],
      status: "completed",
      image: null,
      garments: [],
    },
  ],
  sizes: null,
  garments: [],
  budget: 180,
} as unknown as Project;

describe("styling studio", () => {
  it("requires a selected look before advancing and preserves favorite choice", async () => {
    const onToggle = vi.fn();
    render(
      <LookGallery
        project={project}
        onToggle={onToggle}
        onContinue={vi.fn()}
        onRetry={vi.fn()}
        busy={false}
      />,
    );
    expect(
      screen.getByRole("button", { name: /find my pieces/i }),
    ).toBeDisabled();
    await userEvent.click(
      screen.getByRole("button", { name: /save soft tailoring/i }),
    );
    expect(onToggle).toHaveBeenCalledWith("look-1");
    expect(
      screen.getByText(/Demo lookbook · These illustrations/),
    ).toBeVisible();
  });

  it("collects explicit sizes and sends them without inferring them from photos", async () => {
    const onSubmit = vi.fn();
    render(<FitForm project={project} busy={false} onSubmit={onSubmit} />);
    await userEvent.selectOptions(screen.getByLabelText("Tops"), "M");
    await userEvent.selectOptions(screen.getByLabelText("Outerwear"), "L");
    await userEvent.type(screen.getByLabelText("Trousers"), "W32 L32");
    await userEvent.selectOptions(screen.getByLabelText("Shoes · EU"), "42");
    await userEvent.click(
      screen.getByRole("button", { name: /build my shopping list/i }),
    );
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        tops: "M",
        outerwear: "L",
        bottoms: "W32 L32",
        shoes: "42",
      }),
    );
  });
});
