import type { WorkflowStep } from "@/types";

type WorkflowStripProps = {
  steps: WorkflowStep[];
};

export function WorkflowStrip({ steps }: WorkflowStripProps) {
  if (!steps.length) return null;

  return (
    <ol className="archive-workflow" aria-label="小浣熊工作流">
      {steps.map((step, index) => (
        <li key={step.id} className="archive-workflow__item">
          <div className="archive-workflow__index">{index + 1}</div>
          <div className="archive-workflow__body">
            <div className="archive-workflow__meta">
              <span className="archive-workflow__module">{step.module}</span>
              <span className="archive-workflow__provider">{step.provider}</span>
            </div>
            <p className="archive-workflow__label">{step.label}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
