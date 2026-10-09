import { describe, expect, it } from "vitest";
import { createPdfChunkPlan } from "../../../src/shared/export/pdf-export";

describe("createPdfChunkPlan", () => {
  it("짧은 문서는 하나의 렌더링 청크로 만든다", () => {
    expect(createPdfChunkPlan(2_000, 1_000)).toEqual([{ offset: 0, height: 2_000, pageCount: 2 }]);
  });

  it("긴 문서는 최대 6페이지 단위의 렌더링 청크로 나눈다", () => {
    expect(createPdfChunkPlan(14_000, 1_000)).toEqual([
      { offset: 0, height: 6_000, pageCount: 6 },
      { offset: 6_000, height: 6_000, pageCount: 6 },
      { offset: 12_000, height: 2_000, pageCount: 2 },
    ]);
  });

  it("마지막 페이지의 실제 높이를 보존한다", () => {
    expect(createPdfChunkPlan(6_500, 1_000)).toEqual([
      { offset: 0, height: 6_000, pageCount: 6 },
      { offset: 6_000, height: 500, pageCount: 1 },
    ]);
  });

  it("잘못된 크기에는 렌더링 청크를 만들지 않는다", () => {
    expect(createPdfChunkPlan(0, 1_000)).toEqual([]);
    expect(createPdfChunkPlan(1_000, 0)).toEqual([]);
  });
});
