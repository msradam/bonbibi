// Bonbibi submission video theme. Mirrors brand/theme.json (repo root) --
// keep the two in sync if either changes. Phthalo Green is a
// presentation/branding palette only, never used for the panel's
// safety-critical status/depth colors.
export const theme = {
  color: {
    phthalo: "#123524",
    phthaloMid: "#1f5b3e",
    phthaloLight: "#2c8158",
    jade: "#39a772",
    shamrock: "#50c38b",
    complementary: "#351222",
    paper: "#F5F5F1",
    ink: "#0B1A24",
    inkSecondary: "#4A5760",
    rule: "#B7BBB2",
  },
  font: {
    chrome: "'Jersey 20', monospace",
    computed: "'Jersey 25', monospace",
    prose: "'Noto Sans', system-ui, sans-serif",
  },
} as const;
