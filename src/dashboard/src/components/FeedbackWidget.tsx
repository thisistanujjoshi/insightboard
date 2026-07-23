import { useState } from "react";
import { submitFeedback, type FeedbackRating } from "../api";
import { useFeedbackVariant } from "../useFeedbackVariant";

type Stage = "idle" | "rated" | "submitted";

export default function FeedbackWidget({ tenant }: { tenant: string }) {
  const variant = useFeedbackVariant();
  const [stage, setStage] = useState<Stage>("idle");
  const [rating, setRating] = useState<FeedbackRating | null>(null);
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);

  function pickRating(r: FeedbackRating) {
    setRating(r);
    setStage("rated");
  }

  async function submit() {
    if (!rating) return;
    setError(null);
    try {
      await submitFeedback(tenant, variant, rating, comment.trim() || undefined);
      setStage("submitted");
    } catch {
      setError("Couldn't send feedback — try again in a moment.");
    }
  }

  return (
    <aside className={`feedback feedback--${variant}`} aria-label="Feedback">
      {stage !== "submitted" ? (
        <>
          <p className="feedback-prompt">Is this dashboard useful?</p>
          <div className="feedback-buttons">
            <button
              type="button"
              className={rating === "up" ? "active" : ""}
              onClick={() => pickRating("up")}
              aria-label="Yes, useful"
            >
              👍
            </button>
            <button
              type="button"
              className={rating === "down" ? "active" : ""}
              onClick={() => pickRating("down")}
              aria-label="Not useful"
            >
              👎
            </button>
          </div>
          {stage === "rated" && (
            <>
              <textarea
                placeholder="Anything you'd add? (optional)"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={2}
              />
              <button type="button" className="feedback-submit" onClick={() => void submit()}>
                Send
              </button>
              {error && <p className="error">{error}</p>}
            </>
          )}
        </>
      ) : (
        <p className="feedback-thanks">Thanks — that helps shape what we build next.</p>
      )}
    </aside>
  );
}
