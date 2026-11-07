import { useId } from "react";

interface Props {
  palette?: string[];
  variant?: number;
  className?: string;
  title?: string;
}

/** Native outfit illustration for demo concepts; never a claimed generated user photo. */
export function FashionFigure({
  palette = ["#81856f", "#eee4d1", "#414840"],
  variant = 0,
  className = "",
  title = "Illustrated outfit concept",
}: Props) {
  const id = useId();
  const [outer = "#81856f", top = "#eee4d1", trousers = "#414840"] = palette;
  const knit = variant % 4 === 3;
  return (
    <svg
      className={`fashion-figure ${className}`}
      viewBox="0 0 360 500"
      role="img"
      aria-labelledby={id}
      xmlns="http://www.w3.org/2000/svg"
    >
      <title id={id}>{title}</title>
      <rect
        width="360"
        height="500"
        fill={variant % 2 ? "#e8e3d9" : "#ecebe2"}
      />
      <path d="M255 0h105v500H255z" fill="#d9d6ca" opacity=".22" />
      <path
        d="M0 412H360M275 0v412"
        fill="none"
        stroke="#d5d2c6"
        strokeWidth="1"
      />
      <ellipse cx="184" cy="466" rx="74" ry="8" fill="#333b31" opacity=".1" />
      <path d="M166 113v27l28 6 8-30" fill="#b68b70" />
      <path
        d="M158 66q1-26 26-28 32 2 28 39l-7 30q-10 22-28 10-17-10-19-51"
        fill="#c8a184"
      />
      <path
        d="M157 73q-13-38 22-41 40-3 35 40l-9-16-17 2-10-8-12 24"
        fill={variant % 3 === 0 ? "#3f3a30" : "#4b4035"}
      />
      <path d="M205 76q13-8 9 9l-8 8M160 77q-11-6-7 9l7 8" fill="#c8a184" />
      <path
        d="M178 101q8 4 14-1"
        fill="none"
        stroke="#9f765e"
        strokeWidth="1.3"
        strokeLinecap="round"
      />
      <path
        d="M143 277l-7 92 8 74 30 1 8-140 8 65 8 75 31-4-2-94-13-74"
        fill={trousers}
      />
      <path
        d="M181 300l-4-23M150 301l-5 65M215 300l6 57M202 439h23M147 439h24"
        fill="none"
        stroke="#121b16"
        opacity=".19"
        strokeWidth="2"
      />
      <path
        d="M141 437l-3 17q-14 10-8 15l47-1-1-28M199 437l2 29 48 1q5-5-18-17l-7-12"
        fill={variant === 4 ? "#30332e" : "#e9e3d7"}
      />
      <path
        d="M130 468l47-1M203 466l46 0"
        stroke="#827d70"
        fill="none"
        strokeWidth="2"
      />
      <path
        d="M159 130l-23 18-7 132q34 14 80-1l-2-138-14-10q-18 12-34-1"
        fill={top}
      />
      {variant === 6 && (
        <g stroke="#53606c" strokeWidth="6" opacity=".75">
          <path d="M140 164h65M138 183h68M137 202h69M135 221h72M135 240h72" />
        </g>
      )}
      <path
        d="M158 128l-29 11-17 11-22 105 24 9 25-79-8 102 43 4 3-136-19-27M195 128l29 11 18 19 26 94-25 11-27-75 13 97-40 6-5-137 11-26"
        fill={outer}
      />
      <path
        d="M156 129l-14 33 25 10 9-18M196 130l14 31-18 11-8-18"
        fill="none"
        stroke="#202b20"
        strokeWidth="1.5"
        opacity=".22"
      />
      <path
        d="M93 255l-5 17q-5 22 8 25 9-3 12-26l3-9M245 258l7 21q6 18 16 10 4-6-5-31"
        fill="#c8a184"
      />
      <path
        d="M142 216h24v22h-24zM199 216h21v22h-21z"
        fill="none"
        stroke="#253121"
        opacity=".25"
        strokeWidth="1.5"
      />
      {!knit && (
        <g fill="#404938" opacity=".65">
          <circle cx="176" cy="184" r="2" />
          <circle cx="176" cy="211" r="2" />
          <circle cx="176" cy="239" r="2" />
          <circle cx="176" cy="267" r="2" />
        </g>
      )}
      <path
        d="M118 165l-13 84M233 169l19 79M138 275l29 1M195 276l28-3"
        fill="none"
        stroke="#263021"
        opacity=".16"
        strokeWidth="2"
      />
    </svg>
  );
}
