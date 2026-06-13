import type { AnalyticsPayload } from "@/types";

type AuditAnalyticsProps = {
  analytics: AnalyticsPayload | null;
};

export function AuditAnalytics({ analytics }: AuditAnalyticsProps) {
  if (!analytics) {
    return <p className="text-sm text-[#6b7585]">完成审核后展示合规率、风险分布与效率对比。</p>;
  }

  const { compliance_summary: summary, risk_distribution: risks, group_stats: groups, efficiency } =
    analytics;

  return (
    <div className="archive-analytics space-y-5">
      <div className="archive-analytics__hero">
        <div className="archive-analytics__metric">
          <span className="archive-analytics__value">{analytics.pass_rate}%</span>
          <span className="archive-analytics__label">合规通过率</span>
        </div>
        <div className="archive-analytics__metric">
          <span className="archive-analytics__value">{efficiency.time_saved_percent}%</span>
          <span className="archive-analytics__label">预估时效提升</span>
        </div>
        <div className="archive-analytics__metric">
          <span className="archive-analytics__value">{efficiency.estimated_ai_minutes} 分钟</span>
          <span className="archive-analytics__label">
            vs 人工约 {efficiency.estimated_manual_hours} 小时
          </span>
        </div>
      </div>

      <section>
        <h3 className="archive-analytics__title">规则结论分布</h3>
        <div className="archive-analytics__bars">
          <Bar label="通过" value={summary.passed} total={summary.total} tone="pass" />
          <Bar label="不通过" value={summary.failed} total={summary.total} tone="fail" />
          <Bar label="需复核" value={summary.needs_review} total={summary.total} tone="review" />
        </div>
      </section>

      <section>
        <h3 className="archive-analytics__title">风险等级（不通过项）</h3>
        <div className="archive-analytics__chips">
          <Chip label="高风险" value={risks["高风险"] ?? 0} tone="high" />
          <Chip label="中风险" value={risks["中风险"] ?? 0} tone="medium" />
          <Chip label="低风险" value={risks["低风险"] ?? 0} tone="low" />
        </div>
      </section>

      <section>
        <h3 className="archive-analytics__title">分组通过率</h3>
        <div className="space-y-2">
          {groups.map((group) => (
            <div key={group.group} className="archive-analytics__group">
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="font-medium text-[var(--archive-ink-soft)]">{group.group}</span>
                <span className="font-mono text-xs text-[#6b7585]">
                  {group.passed}/{group.total} · {group.pass_rate}%
                </span>
              </div>
              <div className="archive-analytics__track">
                <div
                  className="archive-analytics__fill"
                  style={{ width: `${group.pass_rate}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {analytics.high_risk_items.length > 0 && (
        <section>
          <h3 className="archive-analytics__title">高风险项速览</h3>
          <ul className="archive-analytics__list">
            {analytics.high_risk_items.map((item) => (
              <li key={`${item.group}-${item.rule}`}>
                <strong>{item.rule}</strong>
                <span className="text-[#6b7585]">（{item.group}）</span>
                <p>{item.evidence}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function Bar({
  label,
  value,
  total,
  tone,
}: {
  label: string;
  value: number;
  total: number;
  tone: "pass" | "fail" | "review";
}) {
  const percent = total ? Math.round((value / total) * 100) : 0;
  return (
    <div className="archive-analytics__bar-row">
      <span className="archive-analytics__bar-label">{label}</span>
      <div className="archive-analytics__track">
        <div
          className={`archive-analytics__fill archive-analytics__fill--${tone}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="archive-analytics__bar-value">
        {value}/{total}
      </span>
    </div>
  );
}

function Chip({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "high" | "medium" | "low";
}) {
  return (
    <div className={`archive-analytics__chip archive-analytics__chip--${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
