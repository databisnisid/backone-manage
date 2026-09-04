import { init, type ECharts, type EChartsCoreOption } from "echarts/core";

/**
 * Manual echarts init/resize/dispose on a DOM element.
 * ponytail: single-series charts mostly; no wrapper lib (lazy rule).
 */
export function useECharts(el: Ref<HTMLElement | null>) {
  let chart: ECharts | null = null;
  let ro: ResizeObserver | null = null;

  function ensure(): ECharts {
    if (!chart) {
      if (!el.value) throw new Error("chart element missing");
      chart = init(el.value);
      ro = new ResizeObserver(() => chart?.resize());
      ro.observe(el.value);
    }
    return chart;
  }

  function setOption(option: EChartsCoreOption) {
    ensure().setOption(option);
  }

  function dispose() {
    ro?.disconnect();
    chart?.dispose();
    chart = null;
  }

  return { setOption, dispose };
}