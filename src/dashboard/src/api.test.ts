import { describe, expect, it } from "vitest";
import { parseAskError } from "./api";

describe("parseAskError", () => {
  it("extracts message and sql from a structured detail object", () => {
    expect(parseAskError({ detail: { message: "Disallowed keyword: drop", sql: "DROP TABLE orders" } }))
      .toEqual({ message: "Disallowed keyword: drop", sql: "DROP TABLE orders" });
  });

  it("handles a plain string detail", () => {
    expect(parseAskError({ detail: "The assistant is currently unavailable." }))
      .toEqual({ message: "The assistant is currently unavailable." });
  });

  it("falls back to a generic message when detail is missing or malformed", () => {
    expect(parseAskError({})).toEqual({ message: "Request failed." });
    expect(parseAskError(null)).toEqual({ message: "Request failed." });
    expect(parseAskError({ detail: { sql: "SELECT 1" } })).toEqual({ message: "Request failed.", sql: "SELECT 1" });
  });
});
