import { useEffect, useState } from "react";

// Validated reference palette (slot 1 + text/grid/status tokens), stepped per mode.
const LIGHT = {
  series: "#2a78d6",
  textPrimary: "#0b0b0b",
  textSecondary: "#52514e",
  grid: "#e4e3df",
  error: "#e34948",     // status "critical" — reserved, used only for anomaly markers
  surface: "#ffffff",
};
const DARK = {
  series: "#3987e5",
  textPrimary: "#ffffff",
  textSecondary: "#c3c2b7",
  grid: "#3a3a38",
  error: "#e66767",
  surface: "#232322",
};

export function usePalette() {
  const [dark, setDark] = useState(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches,
  );
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e: MediaQueryListEvent) => setDark(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return dark ? DARK : LIGHT;
}
