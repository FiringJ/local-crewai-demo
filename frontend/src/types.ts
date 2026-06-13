export type ProviderConfig = {
  label: string;
  model: string;
  base_url: string;
  api_key_env: string;
  api_key_placeholder: string;
};

export type RuleItem = {
  name: string;
  risk: string;
  logic: string;
};

export type CompetitionCapability = {
  id: string;
  module: string;
  label: string;
  icon: string;
};

export type CompetitionInfo = {
  event: string;
  scene: string;
  tagline: string;
  pain_point: string;
  value_proposition: string;
  capabilities: CompetitionCapability[];
  submission_doc: string;
  prompts_doc: string;
};

export type KnowledgeSource = {
  name: string;
  path: string;
  size: string;
};

export type WorkflowStep = {
  id: string;
  module: string;
  label: string;
  provider: string;
  status: string;
};

export type AnalyticsPayload = {
  pass_rate: number;
  compliance_summary: {
    passed: number;
    failed: number;
    needs_review: number;
    total: number;
  };
  risk_distribution: Record<string, number>;
  group_stats: Array<{
    group: string;
    passed: number;
    failed: number;
    needs_review: number;
    total: number;
    pass_rate: number;
  }>;
  high_risk_items: Array<{
    rule: string;
    group: string;
    evidence: string;
  }>;
  efficiency: {
    rules_checked: number;
    estimated_manual_hours: number;
    estimated_ai_minutes: number;
    time_saved_percent: number;
  };
};

export type AppConfig = {
  providers: Record<string, ProviderConfig>;
  reviewModes: Record<string, string>;
  rules: Record<string, RuleItem[]>;
  competition?: CompetitionInfo;
  knowledgeSources?: KnowledgeSource[];
  defaults: {
    provider: string;
    reviewMode: string;
  };
};

export type ReviewResponse = {
  ok: boolean;
  mode?: string;
  model?: string;
  fileName?: string;
  report?: string;
  auditJson?: string;
  analytics?: AnalyticsPayload;
  briefing?: string;
  workflow?: WorkflowStep[];
  knowledgeSources?: KnowledgeSource[];
  reportPath?: string;
  logs?: string;
  error?: string;
  traceback?: string;
};

export type StatusMode = "idle" | "busy" | "error" | "success" | "fallback";
