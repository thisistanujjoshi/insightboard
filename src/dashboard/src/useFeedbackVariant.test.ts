import { describe, expect, it } from "vitest";
import { pickVariant } from "./useFeedbackVariant";

describe("pickVariant", () => {
  it("reuses a previously stored sidebar assignment", () => {
    expect(pickVariant("sidebar", () => 0.99)).toBe("sidebar");
  });

  it("reuses a previously stored footer assignment", () => {
    expect(pickVariant("footer", () => 0.01)).toBe("footer");
  });

  it("ignores garbage stored values and assigns fresh", () => {
    expect(pickVariant("banner", () => 0.1)).toBe("sidebar");
    expect(pickVariant(null, () => 0.9)).toBe("footer");
  });

  it("splits at the midpoint of the random source", () => {
    expect(pickVariant(null, () => 0)).toBe("sidebar");
    expect(pickVariant(null, () => 0.4999)).toBe("sidebar");
    expect(pickVariant(null, () => 0.5)).toBe("footer");
    expect(pickVariant(null, () => 0.9999)).toBe("footer");
  });
});
