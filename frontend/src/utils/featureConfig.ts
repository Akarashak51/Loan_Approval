/**
 * Mirrors ml/preprocessing/feature_config.py -- the application form is
 * generated from this so fields always match the actual model features
 * (spec section 14: DO NOT invent fields not used by the model).
 * If you add/remove a feature in the Python config, update this too.
 */

export type FeatureCategory = 'numeric' | 'categorical';

export interface FeatureDef {
  label: string;
  category: FeatureCategory;
  options?: string[];
  optionLabels?: Record<string, string>;
  min?: number;
  max?: number;
  mutable: boolean;
  section: 'Applicant' | 'Financial' | 'Loan' | 'Assets';
  helper?: string;
}

/**
 * The model was trained on a legacy dataset whose categorical values contain
 * "DM" internally. Keep those values unchanged for the API, but never show
 * that legacy currency in the Indian-facing interface.
 */
export function formatCurrencyValue(value: unknown): string {
  return String(value).replace(/DM/g, '₹');
}

export function formatINR(value: number | string): string {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return '₹0';
  return `₹${Math.round(amount).toLocaleString('en-IN')}`;
}

export function formatModelFeatureValue(feature: string, value: unknown): string {
  if (feature === 'credit_amount') return formatINR(Number(value) * 100);
  const labels: Record<string, Record<string, string>> = {
    checking_account_status: { 'no checking account': 'No active current account', '< 0 DM': 'Below ₹10,000', '0-200 DM': '₹10,000 – ₹50,000', '>= 200 DM': 'Above ₹50,000' },
    savings_account: { '< 100 DM': 'Below ₹10,000', '100-500 DM': '₹10,000 – ₹50,000', '500-1000 DM': '₹50,000 – ₹1,00,000', '>= 1000 DM': 'Above ₹1,00,000', 'unknown/no savings account': 'Not available' },
  };
  return labels[feature]?.[String(value)] ?? formatCurrencyValue(value);
}

export const FEATURES: Record<string, FeatureDef> = {
  checking_account_status: {
    label: 'Current Account Balance', category: 'categorical',
    options: ['no_account', 'below_10000', '10000_50000', 'above_50000'],
    optionLabels: { no_account: 'No active current account', below_10000: 'Below ₹10,000', 10000_50000: '₹10,000 – ₹50,000', above_50000: 'Above ₹50,000' },
    mutable: true, section: 'Financial', helper: 'Choose the range closest to your current account balance.',
  },
  duration_months: {
    label: 'Loan Duration (months)', category: 'numeric', min: 4, max: 72, mutable: true, section: 'Loan',
  },
  credit_history: {
    label: 'Credit History', category: 'categorical',
    options: [
      'no credits taken', 'all credits paid back duly (this bank)',
      'existing credits paid back duly till now', 'delay in past payments',
      'critical account / other credits existing',
    ], mutable: true, section: 'Loan',
  },
  purpose: {
    label: 'Loan Purpose', category: 'categorical',
    options: ['home_loan', 'car_loan', 'two_wheeler', 'education', 'personal_loan', 'medical', 'business', 'home_renovation', 'consumer_purchase', 'other'],
    optionLabels: { home_loan: 'Home Loan', car_loan: 'Car Loan', two_wheeler: 'Two-Wheeler Loan', education: 'Education Loan', personal_loan: 'Personal Loan', medical: 'Medical Loan', business: 'Business Loan', home_renovation: 'Home Renovation', consumer_purchase: 'Consumer Purchase', other: 'Other' },
    mutable: true, section: 'Loan',
  },
  credit_amount: {
    label: 'Loan Amount (₹)', category: 'numeric', min: 25000, max: 2000000, mutable: true, section: 'Financial', helper: 'Recommended range: ₹25,000 – ₹20,00,000.',
  },
  savings_account: {
    label: 'Savings Account Balance (₹)', category: 'categorical',
    options: ['below_10000', '10000_50000', '50000_100000', 'above_100000', 'unknown'],
    optionLabels: { below_10000: 'Below ₹10,000', 10000_50000: '₹10,000 – ₹50,000', 50000_100000: '₹50,000 – ₹1,00,000', above_100000: 'Above ₹1,00,000', unknown: 'Not available' },
    mutable: true, section: 'Assets',
  },
  employment_since: {
    label: 'Employment Duration', category: 'categorical',
    options: ['unemployed', '< 1 year', '1-4 years', '4-7 years', '>= 7 years'], mutable: true, section: 'Applicant',
  },
  installment_rate_percent: {
    label: 'Installment Rate (% of income)', category: 'numeric', min: 1, max: 4, mutable: true, section: 'Financial',
  },
  personal_status_sex: {
    label: 'Personal Status', category: 'categorical',
    options: [
      'male:divorced/separated', 'female:divorced/separated/married',
      'male:single', 'male:married/widowed', 'female:single',
    ], mutable: false, section: 'Applicant',
  },
  other_debtors_guarantors: {
    label: 'Other Debtors / Guarantors', category: 'categorical',
    options: ['none', 'co-applicant', 'guarantor'], mutable: true, section: 'Financial',
  },
  present_residence_since: {
    label: 'Years at Current Residence', category: 'numeric', min: 0, max: 50, mutable: true, section: 'Applicant',
  },
  property: {
    label: 'Property', category: 'categorical',
    options: ['real estate', 'building society savings/life insurance', 'car or other', 'unknown/no property'], mutable: true, section: 'Assets',
  },
  age: {
    label: 'Age', category: 'numeric', min: 18, max: 100, mutable: false, section: 'Applicant',
  },
  other_installment_plans: {
    label: 'Other Installment Plans', category: 'categorical',
    options: ['bank', 'stores', 'none'], mutable: true, section: 'Loan',
  },
  housing: {
    label: 'Housing', category: 'categorical',
    options: ['rent', 'own', 'for free'], mutable: true, section: 'Assets',
  },
  existing_credits_count: {
    label: 'Existing Credit Accounts', category: 'numeric', min: 0, max: 10, mutable: true, section: 'Financial',
  },
  job: {
    label: 'Job Category', category: 'categorical',
    options: [
      'unemployed/unskilled non-resident', 'unskilled resident',
      'skilled employee/official', 'management/self-employed/highly qualified',
    ], mutable: true, section: 'Applicant',
  },
  num_dependents: {
    label: 'Number of Dependents', category: 'numeric', min: 0, max: 10, mutable: true, section: 'Applicant',
  },
  telephone: {
    label: 'Registered Telephone', category: 'categorical',
    options: ['none', 'registered'], mutable: true, section: 'Applicant',
  },
  foreign_worker: {
    label: 'Foreign Worker', category: 'categorical',
    options: ['yes', 'no'], mutable: false, section: 'Applicant',
  },
};

export const FEATURE_KEYS = Object.keys(FEATURES);

export function emptyApplicantForm(): Record<string, string> {
  return Object.fromEntries(FEATURE_KEYS.map((k) => [k, '']));
}
