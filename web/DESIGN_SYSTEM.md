# Axon — Design System

**Monochrome professional** — black background, white text, restrained.
Reference points: Linear / Vercel dashboards. Color appears only as a status signal.

## Typography
- **Inter** for everything (400/500/600/700). Tight, professional letter-spacing on headings.
- Tabular figures (`font-variant-numeric: tabular-nums`) for all numbers.
- Monospace (system) only for the reasoning trace and evidence-source tags.

## Color tokens
| Role | Token | Hex |
|------|-------|-----|
| Background | `--bg` | `#000000` |
| Panel / card | `--surface` | `#0d0d0d` |
| Raised surface | `--surface-2` | `#161616` |
| Border | `--border` | `#232323` |
| Strong border | `--border-strong` | `#333333` |
| Text | `--text` | `#ffffff` |
| Secondary text | `--muted` | `#8f8f8f` |
| Status — healthy | `--green` | `#3fb950` |
| Status — watch | `--amber` | `#d29922` |
| Status — risk | `--red` | `#f85149` |

- **Primary CTA** = white button, black text (the only high-emphasis element).
- Status colors are used **only** on the thin confidence bar + small tags — never as fills or decoration.

## Layout & motion
- KPI strip (monochrome) over the recommendation feed; 290px sidebar.
- Flat surfaces, 1px borders, no gradients or shadows (except the toast).
- Subtle 0.22s fade-in on cards/KPIs; skeleton loaders while the planner runs.
- All motion wrapped in `@media (prefers-reduced-motion: no-preference)`.

## Principles
Restraint over decoration · high contrast · one accent of emphasis (white) · color = meaning, not style.
