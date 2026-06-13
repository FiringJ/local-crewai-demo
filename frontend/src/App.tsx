import { Loader2, Play } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { AuditAnalytics } from "@/components/AuditAnalytics";
import { ArchivePanel } from "@/components/ArchivePanel";
import { Atmosphere } from "@/components/Atmosphere";
import { CapabilityBadges } from "@/components/CapabilityBadges";
import { FileDropzone } from "@/components/FileDropzone";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import { WorkflowStrip } from "@/components/WorkflowStrip";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { fetchConfig, submitReview } from "@/lib/api";
import type { AnalyticsPayload, AppConfig, StatusMode, WorkflowStep } from "@/types";

const STATUS_LABEL: Record<StatusMode, string> = {
  idle: "待命",
  busy: "审核中",
  error: "失败",
  success: "完成",
  fallback: "已回退",
};

function statusClass(mode: StatusMode) {
  return `status-pill status-pill--${mode}`;
}

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loadError, setLoadError] = useState("");
  const [statusMode, setStatusMode] = useState<StatusMode>("idle");
  const [running, setRunning] = useState(false);

  const [contractFile, setContractFile] = useState<File | null>(null);
  const [contractText, setContractText] = useState("");
  const [reviewMode, setReviewMode] = useState("");
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [apiKeyPlaceholder, setApiKeyPlaceholder] = useState("仅本次运行使用");

  const [activeTab, setActiveTab] = useState("report");
  const [report, setReport] = useState("上传合同文件，或粘贴合同正文后开始审核。");
  const [auditJson, setAuditJson] = useState("");
  const [analytics, setAnalytics] = useState<AnalyticsPayload | null>(null);
  const [briefing, setBriefing] = useState("");
  const [workflow, setWorkflow] = useState<WorkflowStep[]>([]);
  const [logs, setLogs] = useState("");

  const rulesText = useMemo(
    () => (config ? JSON.stringify(config.rules, null, 2) : ""),
    [config],
  );

  const charCount = contractText.length.toLocaleString("zh-CN");

  useEffect(() => {
    fetchConfig()
      .then((data) => {
        setConfig(data);
        setProvider(data.defaults.provider);
        setReviewMode(data.defaults.reviewMode);
        const selected = data.providers[data.defaults.provider];
        if (selected) {
          setModel(selected.model);
          setBaseUrl(selected.base_url);
          setApiKeyPlaceholder(
            selected.api_key_placeholder
              ? `默认：${selected.api_key_placeholder}`
              : "仅本次运行使用",
          );
        }
      })
      .catch((error: Error) => {
        setLoadError(error.message);
        setStatusMode("error");
        setReport(error.message);
      });
  }, []);

  const applyProvider = (providerKey: string) => {
    if (!config) return;
    const selected = config.providers[providerKey];
    if (!selected) return;
    setModel(selected.model);
    setBaseUrl(selected.base_url);
    setApiKeyPlaceholder(
      selected.api_key_placeholder
        ? `默认：${selected.api_key_placeholder}`
        : "仅本次运行使用",
    );
  };

  const handleProviderChange = (value: string | null) => {
    if (!value) return;
    setProvider(value);
    applyProvider(value);
  };

  const handleReview = async () => {
    if (!contractFile && !contractText.trim()) {
      setStatusMode("error");
      setReport("请上传合同文件，或粘贴合同正文。");
      setActiveTab("report");
      return;
    }

    setRunning(true);
    setStatusMode("busy");
    setReport("正在审核...");
    setAuditJson("");
    setAnalytics(null);
    setBriefing("");
    setWorkflow([]);
    setLogs("");
    setActiveTab("report");

    try {
      const data = await submitReview({
        contractFile,
        contractText,
        reviewMode,
        provider,
        model,
        baseUrl,
        apiKey,
      });

      if (!data.ok) {
        setStatusMode("error");
        setReport(data.error || "审核失败。");
        setLogs(data.traceback || data.logs || "");
        return;
      }

      setStatusMode(data.mode === "rules_fallback" ? "fallback" : "success");
      setReport(data.report || "");
      setAuditJson(data.auditJson || "");
      setAnalytics(data.analytics ?? null);
      setBriefing(data.briefing || "");
      setWorkflow(data.workflow ?? []);
      setLogs(data.logs || "");
    } catch (error) {
      setStatusMode("error");
      setReport(error instanceof Error ? error.message : "审核失败。");
    } finally {
      setRunning(false);
    }
  };

  if (loadError && !config) {
    return (
      <div className="archive-app flex min-h-svh items-center justify-center p-6">
        <Atmosphere />
        <ArchivePanel className="w-full max-w-lg p-6">
          <h2 className="archive-panel__title">加载失败</h2>
          <p className="mt-2 text-sm text-[#6b7585]">{loadError}</p>
        </ArchivePanel>
      </div>
    );
  }

  return (
    <div className="archive-app">
      <Atmosphere />

      <header className="archive-header">
        <div className="archive-header__inner">
          <div className="archive-header__row">
            <div className="archive-brand">
              <p className="archive-eyebrow">
                {config?.competition?.event ?? "商汤小浣熊 OPC 高手创造赛"}
              </p>
              <h1 className="archive-title">
                {config?.competition?.scene ?? "企业合同初审工作台"}
              </h1>
              <p className="archive-tagline">
                {config?.competition?.tagline ??
                  "一人 + 办公小浣熊，跑通法务初审全链路"}
              </p>
            </div>

            <div className="archive-header__aside">
              <dl className="archive-metrics" aria-label="效能指标">
                <div className="archive-metrics__item">
                  <dt>规则</dt>
                  <dd>22</dd>
                </div>
                <div className="archive-metrics__item">
                  <dt>耗时</dt>
                  <dd>≈3min</dd>
                </div>
                <div className="archive-metrics__item">
                  <dt>模块</dt>
                  <dd>5</dd>
                </div>
              </dl>
              <div className={statusClass(statusMode)} role="status" aria-live="polite">
                <span className="status-pill__dot" aria-hidden="true" />
                {STATUS_LABEL[statusMode]}
              </div>
            </div>
          </div>

          {config?.competition?.capabilities && (
            <CapabilityBadges capabilities={config.competition.capabilities} />
          )}
        </div>
      </header>

      <main className="archive-layout">
        <ArchivePanel className="archive-panel-enter h-fit self-start">
          <div className="archive-panel__head">
            <span className="archive-panel__title">审核输入</span>
            <span className="archive-panel__desc">办公小浣熊全链路</span>
          </div>

          <div className="archive-panel__body space-y-5">
            <div className="space-y-2">
              <Label className="archive-field-label">
                <span>合同文件</span>
              </Label>
              <FileDropzone file={contractFile} onFileChange={setContractFile} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="contractText" className="archive-field-label">
                <span>合同正文</span>
                <span className="archive-field-meta">{charCount} 字</span>
              </Label>
              <Textarea
                id="contractText"
                rows={7}
                spellCheck={false}
                placeholder="或直接粘贴合同全文…"
                value={contractText}
                onChange={(event) => setContractText(event.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label className="archive-field-label">审核模式</Label>
              <Select value={reviewMode} onValueChange={(value) => value && setReviewMode(value)}>
                <SelectTrigger className="w-full">
                  <SelectValue>
                    {config?.reviewModes[reviewMode] ?? "选择审核模式"}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {config &&
                    Object.entries(config.reviewModes).map(([key, label]) => (
                      <SelectItem key={key} value={key}>
                        {label}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <Button className="archive-cta" size="lg" onClick={handleReview} disabled={running}>
              {running ? <Loader2 className="animate-spin" /> : <Play className="fill-current" />}
              开始审核
            </Button>

            <div className="archive-divider">
              <span>模型配置</span>
            </div>

            <div className="space-y-1">
              <p className="archive-panel__title text-[15px]">LLM 连接</p>
              <p className="text-xs text-[#6b7585]">默认办公小浣熊 / SenseNova</p>
            </div>

            <div className="grid gap-4">
              <div className="space-y-2">
                <Label className="archive-field-label">Provider</Label>
                <Select value={provider} onValueChange={handleProviderChange}>
                  <SelectTrigger className="w-full">
                    <SelectValue>
                      {config?.providers[provider]?.label ?? "选择 Provider"}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {config &&
                      Object.entries(config.providers).map(([key, value]) => (
                        <SelectItem key={key} value={key}>
                          {value.label}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="model" className="archive-field-label">
                  Model
                </Label>
                <Input
                  id="model"
                  value={model}
                  autoComplete="off"
                  onChange={(event) => setModel(event.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="baseUrl" className="archive-field-label">
                  Base URL
                </Label>
                <Input
                  id="baseUrl"
                  value={baseUrl}
                  autoComplete="off"
                  onChange={(event) => setBaseUrl(event.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="apiKey" className="archive-field-label">
                  API Key
                </Label>
                <Input
                  id="apiKey"
                  type="password"
                  value={apiKey}
                  autoComplete="off"
                  placeholder={apiKeyPlaceholder}
                  onChange={(event) => setApiKey(event.target.value)}
                />
              </div>
            </div>
          </div>
        </ArchivePanel>

        <ArchivePanel className="archive-panel-enter flex min-h-[560px] flex-col">
          <Tabs
            value={activeTab}
            onValueChange={(value) => value && setActiveTab(value)}
            className="flex min-h-0 flex-1 flex-col"
          >
            <div className="archive-panel__head archive-panel__head--tabs">
              <TabsList className="archive-tabs-list">
                <TabsTrigger value="report">审核报告</TabsTrigger>
                <TabsTrigger value="analytics">数据洞察</TabsTrigger>
                <TabsTrigger value="briefing">汇报大纲</TabsTrigger>
                <TabsTrigger value="workflow">工作流</TabsTrigger>
                <TabsTrigger value="json">JSON</TabsTrigger>
                <TabsTrigger value="rules">规则</TabsTrigger>
                <TabsTrigger value="logs">日志</TabsTrigger>
              </TabsList>
              <span className="archive-panel__desc">小浣熊交付物</span>
            </div>

            <TabsContent value="report" className="m-0 flex-1 min-h-0">
              <OutputPane content={report} markdown />
            </TabsContent>
            <TabsContent value="analytics" className="m-0 flex-1 min-h-0">
              <ScrollArea className="archive-output-pane">
                <div className="archive-output-text p-4">
                  <AuditAnalytics analytics={analytics} />
                </div>
              </ScrollArea>
            </TabsContent>
            <TabsContent value="briefing" className="m-0 flex-1 min-h-0">
              <OutputPane
                content={briefing || "完成审核后生成 6 页管理层汇报大纲，可粘贴至办公小浣熊 PPT 生成。"}
                markdown
              />
            </TabsContent>
            <TabsContent value="workflow" className="m-0 flex-1 min-h-0">
              <ScrollArea className="archive-output-pane">
                <div className="archive-output-text p-4">
                  <WorkflowStrip steps={workflow} />
                  {!workflow.length && (
                    <p className="text-sm text-[#6b7585]">审核完成后展示五模块协同路径。</p>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>
            <TabsContent value="json" className="m-0 flex-1 min-h-0">
              <OutputPane content={auditJson} mono />
            </TabsContent>
            <TabsContent value="rules" className="m-0 flex-1 min-h-0">
              <OutputPane content={rulesText} mono />
            </TabsContent>
            <TabsContent value="logs" className="m-0 flex-1 min-h-0">
              <OutputPane content={logs} mono />
            </TabsContent>
          </Tabs>
        </ArchivePanel>
      </main>
    </div>
  );
}

function OutputPane({
  content,
  mono = false,
  markdown = false,
}: {
  content: string;
  mono?: boolean;
  markdown?: boolean;
}) {
  const isEmpty = !content;

  return (
    <ScrollArea className="archive-output-pane">
      <div
        className={`archive-output-text ${mono ? "archive-output-text--mono" : ""} ${
          isEmpty ? "archive-output-text--empty" : ""
        }`}
      >
        {isEmpty ? (
          "暂无内容"
        ) : markdown ? (
          <ReportMarkdown content={content} />
        ) : (
          <pre className="m-0 whitespace-pre-wrap font-[inherit]">{content}</pre>
        )}
      </div>
    </ScrollArea>
  );
}
