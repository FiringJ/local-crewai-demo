import type { AppConfig, ReviewResponse } from "@/types";

export async function fetchConfig(): Promise<AppConfig> {
  const response = await fetch("/api/config");
  if (!response.ok) {
    throw new Error("无法加载配置");
  }
  return response.json() as Promise<AppConfig>;
}

export type ReviewPayload = {
  contractFile: File | null;
  contractText: string;
  reviewMode: string;
  provider: string;
  model: string;
  baseUrl: string;
  apiKey: string;
};

export async function submitReview(payload: ReviewPayload): Promise<ReviewResponse> {
  const formData = new FormData();
  if (payload.contractFile) {
    formData.append("contract", payload.contractFile, payload.contractFile.name);
  }
  formData.append("contractText", payload.contractText);
  formData.append(
    "fileName",
    payload.contractFile ? payload.contractFile.name : "pasted_contract.txt",
  );
  formData.append("reviewMode", payload.reviewMode);
  formData.append("provider", payload.provider);
  formData.append("model", payload.model);
  formData.append("baseUrl", payload.baseUrl);
  formData.append("apiKey", payload.apiKey);

  const response = await fetch("/api/review", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("审核请求失败");
  }

  return response.json() as Promise<ReviewResponse>;
}
