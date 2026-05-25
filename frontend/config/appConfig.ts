function numberFromEnv(value: string | undefined, fallback: number): number {
  if (!value) return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export const appConfig = {
  brandName: process.env.NEXT_PUBLIC_BRAND_NAME ?? "EAC Timesheets",
  brandSubtitle: process.env.NEXT_PUBLIC_BRAND_SUBTITLE ?? "Weekly Capital Labor Intelligence",
  brandImageSrc: process.env.NEXT_PUBLIC_BRAND_IMAGE_SRC ?? "",
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001",
  appTitle: process.env.NEXT_PUBLIC_APP_TITLE ?? "Weekly Timesheet Classification Dashboard",
  appDescription:
    process.env.NEXT_PUBLIC_APP_DESCRIPTION ??
    "Deterministic, source-agnostic CapEx / OpEx classification for employee activity review.",
  reviewerViewLabel: process.env.NEXT_PUBLIC_REVIEWER_VIEW_LABEL ?? "Finance Reviewer View",
  ruleVersion: process.env.NEXT_PUBLIC_RULE_VERSION ?? "fixed-asset-policy-v1.0",
  personaName: process.env.NEXT_PUBLIC_PERSONA_NAME ?? "Project Coder Weekly Timesheet",
  reviewThreshold: numberFromEnv(process.env.NEXT_PUBLIC_REVIEW_THRESHOLD, 70),
  semanticStoreLabel: process.env.NEXT_PUBLIC_SEMANTIC_STORE_LABEL ?? "pgvector",
  decisionAuthorityLabel:
    process.env.NEXT_PUBLIC_DECISION_AUTHORITY_LABEL ?? "Policy-led deterministic rules"
};
