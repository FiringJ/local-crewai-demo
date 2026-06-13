import { Fragment } from "react";

import type { CompetitionCapability } from "@/types";

type CapabilityBadgesProps = {
  capabilities: CompetitionCapability[];
};

export function CapabilityBadges({ capabilities }: CapabilityBadgesProps) {
  return (
    <nav className="archive-pipeline" aria-label="办公小浣熊能力链路">
      <p className="archive-pipeline__legend">能力链路</p>
      <div className="archive-pipeline__track">
        {capabilities.map((item, index) => (
          <Fragment key={item.id}>
            {index > 0 && <span className="archive-pipeline__connector" aria-hidden="true" />}
            <div className="archive-pipeline__node" title={item.label}>
              <span className="archive-pipeline__index">{String(index + 1).padStart(2, "0")}</span>
              <span className="archive-pipeline__name">{item.module}</span>
              <span className="archive-pipeline__hint">{item.label}</span>
            </div>
          </Fragment>
        ))}
      </div>
    </nav>
  );
}
