import { Composition } from "remotion";
import { NinjaIntro } from "./NinjaIntro";
import { BenchmarkChart, defaultBenchmarkProps } from "./BenchmarkChart";
import {
  CopilotExplainer,
  defaultCopilotProps,
  TOTAL_FRAMES,
} from "./CopilotExplainer";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="NinjaIntro"
        component={NinjaIntro}
        durationInFrames={195}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="BenchmarkChart"
        component={BenchmarkChart}
        durationInFrames={210}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultBenchmarkProps}
      />
      <Composition
        id="CopilotExplainer"
        component={CopilotExplainer}
        durationInFrames={TOTAL_FRAMES}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={defaultCopilotProps}
      />
      <Composition
        id="CopilotExplainerMusic"
        component={CopilotExplainer}
        durationInFrames={TOTAL_FRAMES}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ withMusic: true }}
      />
    </>
  );
};
