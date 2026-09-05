/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0B0E14",
        panel: "#12161F",
        line: "rgba(255,255,255,0.08)",
        muted: "#8A93A6",
        // Primary UI accent — evidence-tag amber, used sparingly for the
        // single bold element (active tab, primary button, links).
        amber: { DEFAULT: "#C98A3A", light: "#E0AB63" },
        // Verification outcomes ONLY — never decorative elsewhere.
        teal: { DEFAULT: "#22B8A0", dim: "rgba(34,184,160,0.12)" },
        alert: { DEFAULT: "#E2504C", dim: "rgba(226,80,76,0.12)" },
        // Per-module identity colors (folder-tab spines in the log table).
        typeblue: { DEFAULT: "#5C8DFF", dim: "rgba(92,141,255,0.12)" },
        typeviolet: { DEFAULT: "#9B7BEA", dim: "rgba(155,123,234,0.12)" },
      },
      fontFamily: {
        // Preference stacks, not next/font-fetched — zero external
        // network dependency at build OR runtime, matching this
        // project's offline-capability requirement. Renders as Space
        // Grotesk / IBM Plex Mono on a machine that happens to have
        // them installed, and falls back cleanly to system stacks
        // otherwise. Add a self-hosted font file or a <link> tag if
        // you want the exact typeface guaranteed on every machine.
        display: [
          '"Space Grotesk"', "ui-sans-serif", "system-ui",
          "-apple-system", '"Segoe UI"', "sans-serif",
        ],
        mono: [
          '"IBM Plex Mono"', "ui-monospace", '"SFMono-Regular"',
          '"Cascadia Code"', "Menlo", "Consolas", "monospace",
        ],
      },
    },
  },
  plugins: [],
};
