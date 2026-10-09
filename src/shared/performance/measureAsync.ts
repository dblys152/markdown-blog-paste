let measureSequence = 0;

export async function measureAsync<T>(name: string, task: () => Promise<T>): Promise<T> {
  if (typeof performance === "undefined" || typeof performance.mark !== "function" || typeof performance.measure !== "function") {
    return task();
  }

  const markName = `${name}:start:${measureSequence++}`;
  try {
    performance.mark(markName);
  } catch {
    return task();
  }
  try {
    return await task();
  } finally {
    try {
      performance.measure(name, markName);
    } catch {
      // 성능 측정 실패가 실제 사용자 작업을 방해하지 않게 합니다.
    } finally {
      try {
        performance.clearMarks?.(markName);
      } catch {
        // 측정 항목 정리 실패도 사용자 작업과 분리합니다.
      }
    }
  }
}
