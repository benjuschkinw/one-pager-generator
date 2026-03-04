/**
 * TypeScript types matching the backend Pydantic models.
 */

export type CriterionStatus = "fulfilled" | "questions" | "not_interest";

export interface Meta {
  source: string;
  im_received: string;
  loi_deadline: string;
  status: string;
}

export interface Header {
  label: string;
  company_name: string;
  tagline: string;
}

export interface KeyFacts {
  founded: string;
  hq: string;
  website: string;
  industry: string;
  niche: string;
  revenue: string;
  revenue_year: string;
  ebitda: string;
  ebitda_year: string;
  management: string[];
  employees: string;
}

export interface InvestmentRationale {
  pros: string[];
  cons: string[];
}

export interface RevenueSegment {
  name: string;
  pct: number;
  growth?: string;
}

export interface RevenueSplit {
  segments: RevenueSegment[];
  total: string;
}

export interface Financials {
  years: string[];
  revenue: (number | null)[];
  ebitda: (number | null)[];
  ebitda_margin: (number | null)[];
  da_pct: number | null;
}

export interface InvestmentCriteria {
  ebitda_1m: CriterionStatus;
  dach: CriterionStatus;
  ebitda_margin_10: CriterionStatus;
  majority_stake: CriterionStatus;
  revenue_split: CriterionStatus;
  digitization: CriterionStatus;
  asset_light: CriterionStatus;
  buy_and_build: CriterionStatus;
  esg: CriterionStatus;
  market_fragmentation: CriterionStatus;
  acquisition_vertical: CriterionStatus;
  acquisition_horizontal: CriterionStatus;
  acquisition_geographical: CriterionStatus;
}

export interface OnePagerData {
  meta: Meta;
  header: Header;
  investment_thesis: string;
  key_facts: KeyFacts;
  description: string[];
  product_portfolio: string[];
  investment_rationale: InvestmentRationale;
  revenue_split: RevenueSplit;
  financials: Financials;
  investment_criteria: InvestmentCriteria;
}

export interface FieldFlag {
  field: string;
  severity: "error" | "warning" | "info";
  message: string;
}

export interface VerificationResult {
  verified: boolean;
  confidence: number;
  flags: FieldFlag[];
  verifier_model: string;
}

export interface ResearchResponse {
  data: OnePagerData;
  verification: VerificationResult | null;
}

export interface PromptDefinition {
  name: string;
  description: string;
  template: string;
  is_default: boolean;
}

export const EMPTY_ONE_PAGER: OnePagerData = {
  meta: { source: "", im_received: "", loi_deadline: "", status: "" },
  header: { label: "One Pager", company_name: "", tagline: "" },
  investment_thesis: "",
  key_facts: {
    founded: "",
    hq: "",
    website: "",
    industry: "",
    niche: "",
    revenue: "",
    revenue_year: "",
    ebitda: "",
    ebitda_year: "",
    management: [],
    employees: "",
  },
  description: [],
  product_portfolio: [],
  investment_rationale: { pros: [], cons: [] },
  revenue_split: { segments: [], total: "" },
  financials: {
    years: [],
    revenue: [],
    ebitda: [],
    ebitda_margin: [],
    da_pct: null,
  },
  investment_criteria: {
    ebitda_1m: "questions",
    dach: "questions",
    ebitda_margin_10: "questions",
    majority_stake: "questions",
    revenue_split: "questions",
    digitization: "questions",
    asset_light: "questions",
    buy_and_build: "questions",
    esg: "questions",
    market_fragmentation: "questions",
    acquisition_vertical: "questions",
    acquisition_horizontal: "questions",
    acquisition_geographical: "questions",
  },
};

/** Labels for the investment criteria keys */
export const CRITERIA_LABELS: Record<keyof InvestmentCriteria, string> = {
  ebitda_1m: "EBITDA (EUR 1.0m)",
  dach: "DACH",
  ebitda_margin_10: "EBITDA Margin (10%)",
  majority_stake: "Majority Stake",
  revenue_split: "Revenue Split",
  digitization: "Digitization Potential",
  asset_light: "Asset Light",
  buy_and_build: "Buy & Build Potential",
  esg: "ESG",
  market_fragmentation: "Market Fragmentation",
  acquisition_vertical: "Acquisition: Vertical",
  acquisition_horizontal: "Acquisition: Horizontal",
  acquisition_geographical: "Acquisition: Geographical",
};
