import { useState } from "react";
import type { FeedbackVariant } from "./api";

const STORAGE_KEY = "insightboard_feedback_variant";

/** Pure assignment rule, unit-testable without a DOM: reuse a stored variant,
 * otherwise split 50/50 on the supplied random source. */
export function pickVariant(stored: string | null, random: () => number = Math.random): FeedbackVariant {
  if (stored === "sidebar" || stored === "footer") return stored;
  return random() < 0.5 ? "sidebar" : "footer";
}

/**
 * Assigns each browser to one arm of the feedback-widget placement A/B test
 * (PRD: "one A/B test on its placement") and sticks with it via localStorage,
 * so a returning visitor always sees the same variant.
 */
export function useFeedbackVariant(): FeedbackVariant {
  const [variant] = useState<FeedbackVariant>(() => {
    const assigned = pickVariant(localStorage.getItem(STORAGE_KEY));
    localStorage.setItem(STORAGE_KEY, assigned);
    return assigned;
  });
  return variant;
}
