import { afterEach, describe, expect, it, vi } from "vitest";
import { measureAsync } from "../../../src/shared/performance/measureAsync";

describe("measureAsync", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("비동기 작업의 성공과 실패 모두 User Timing 항목으로 기록한다", async () => {
    const mark = vi.fn();
    const measure = vi.fn();
    const clearMarks = vi.fn();
    vi.stubGlobal("performance", { mark, measure, clearMarks });

    await expect(measureAsync("success", async () => "완료")).resolves.toBe("완료");
    await expect(measureAsync("failure", async () => {
      throw new Error("실패");
    })).rejects.toThrow("실패");

    expect(mark).toHaveBeenCalledTimes(2);
    expect(measure).toHaveBeenCalledWith("success", expect.stringMatching(/^success:start:/));
    expect(measure).toHaveBeenCalledWith("failure", expect.stringMatching(/^failure:start:/));
    expect(clearMarks).toHaveBeenCalledTimes(2);
  });
});
