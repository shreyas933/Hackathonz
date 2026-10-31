export type UserType = 'admin' | 'staff' | 'customer';
export type StaffRole = 'sales' | 'finance';
export type CustomerRole = 'owner' | 'finance_contact' | 'subscription_manager';

export interface User {
  id: number;
  email: string;
  full_name: string;
  user_type: UserType;
  role: string;
  business_id?: number | null;
  is_active: boolean;
  created_at?: string;
  staff_profile?: {
    staff_role: StaffRole;
    department?: string;
    permissions_override?: string;
  };
}

export interface CustomerMember {
  id: number;
  user_id: number;
  email: string;
  full_name: string;
  role: CustomerRole;
  is_primary: boolean;
  created_at: string;
}

export interface CustomerBusiness {
  id: number;
  company_name: string;
  legal_name?: string;
  tax_id?: string;
  billing_address?: string;
  billing_city?: string;
  billing_state?: string;
  billing_postal_code?: string;
  billing_country: string;
  contact_email: string;
  contact_phone?: string;
  status: string;
  created_at: string;
  members?: CustomerMember[];
}

export interface ProductVariant {
  id: number;
  product_id: number;
  variant_name: string;
  sku: string;
  price_adjustment: string;
  attributes_json?: string;
  is_active: boolean;
}

export interface Plan {
  id: number;
  product_id: number;
  name: string;
  code: string;
  billing_frequency: 'daily' | 'weekly' | 'monthly' | 'yearly';
  base_price: string;
  min_quantity: number;
  can_pause: boolean;
  can_early_close: boolean;
  auto_close_at_end: boolean;
  auto_renew: boolean;
  trial_days: number;
  is_active: boolean;
}

export interface Product {
  id: number;
  name: string;
  code: string;
  product_type: 'saas' | 'addon' | 'service';
  sales_price: string;
  cost_price: string;
  description?: string;
  notes?: string;
  is_active: boolean;
  variants: ProductVariant[];
  plans: Plan[];
}

export interface TaxRate {
  id: number;
  name: string;
  rate_percent: string;
  is_compound: boolean;
  is_active: boolean;
}

export interface DiscountRule {
  id: number;
  name: string;
  discount_type: 'percentage' | 'fixed_amount';
  value: string;
  min_seats: number;
  min_amount: string;
  max_allowed_sales_discount: string;
  requires_admin_approval: boolean;
  is_active: boolean;
}

export interface AuditLog {
  id: number;
  actor_user_id?: number;
  actor_email?: string;
  actor_role?: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  before_state?: string;
  after_state?: string;
  ip_address?: string;
  created_at: string;
}

// --- Phase 2 Commercial Types ---

export interface RequestActivity {
  id: number;
  request_id: number;
  actor_user_id?: number;
  activity_type: string;
  message: string;
  created_at: string;
}

export interface SubscriptionRequest {
  id: number;
  reference: string;
  business_id: number;
  request_type: 'new_subscription' | 'additional_seats' | 'upgrade' | 'downgrade' | 'renewal' | 'cancellation';
  related_subscription_id?: number;
  product_id?: number;
  plan_id?: number;
  variant_id?: number;
  requested_quantity: number;
  notes?: string;
  status: string;
  assigned_sales_user_id?: number;
  created_by_user_id?: number;
  created_at: string;
  updated_at: string;
  activities: RequestActivity[];
}

export interface QuotationLine {
  id: number;
  product_id: number;
  plan_id: number;
  variant_id?: number;
  description?: string;
  quantity: number;
  unit_price: string;
  discount_percent: string;
  discount_amount: string;
  tax_rate_percent: string;
  tax_amount: string;
  line_total: string;
}

export interface QuotationDecision {
  id: number;
  decision_maker_user_id?: number;
  decision_type: string;
  reason?: string;
  created_at: string;
}

export interface QuotationVersion {
  id: number;
  quotation_id: number;
  version_number: number;
  status: string;
  revision_reason?: string;
  subtotal: string;
  discount_total: string;
  tax_total: string;
  final_total: string;
  payment_terms: string;
  valid_until?: string;
  start_date?: string;
  is_latest: boolean;
  created_by_user_id?: number;
  created_at: string;
  lines: QuotationLine[];
  decisions: QuotationDecision[];
}

export interface Quotation {
  id: number;
  quotation_number: string;
  business_id: number;
  request_id?: number;
  current_version_number: number;
  status: string;
  created_by_user_id?: number;
  created_at: string;
  updated_at: string;
  versions: QuotationVersion[];
}

export interface VersionDiff {
  quotation_number: string;
  base_version_number: number;
  target_version_number: number;
  subtotal_diff: string;
  discount_diff: string;
  tax_diff: string;
  final_total_diff: string;
  changed_fields: string[];
  lines_comparison: {
    plan_id: number;
    description?: string;
    base_quantity: number;
    target_quantity: number;
    quantity_diff: number;
    base_unit_price: string;
    target_unit_price: string;
    base_line_total: string;
    target_line_total: string;
  }[];
}

export interface SubscriptionLine {
  id: number;
  product_id: number;
  variant_id?: number;
  plan_id: number;
  quantity: number;
  unit_price: string;
  tax_rate_percent: string;
  line_total: string;
}

export interface Subscription {
  id: number;
  subscription_number: string;
  business_id: number;
  accepted_quotation_id?: number;
  accepted_quotation_version_id?: number;
  status: string;
  activation_policy: string;
  start_date?: string;
  expiry_date?: string;
  next_billing_date?: string;
  billing_frequency: string;
  payment_terms: string;
  total_recurring_amount: string;
  created_at: string;
  updated_at: string;
  lines: SubscriptionLine[];
}

export interface InvoiceLine {
  id: number;
  product_id: number;
  variant_id?: number;
  plan_id: number;
  description?: string;
  quantity: number;
  unit_price: string;
  discount_amount: string;
  tax_rate_percent: string;
  tax_amount: string;
  line_total: string;
}

export interface PaymentAllocation {
  id: number;
  payment_id: number;
  invoice_id: number;
  allocated_amount: string;
  created_at: string;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  business_id: number;
  subscription_id?: number;
  quotation_version_id?: number;
  billing_period: string;
  issue_date: string;
  due_date: string;
  subtotal: string;
  discount_total: string;
  tax_total: string;
  final_total: string;
  amount_paid: string;
  remaining_balance: string;
  currency: string;
  payment_terms: string;
  status: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  lines: InvoiceLine[];
  allocations: PaymentAllocation[];
}

export interface Payment {
  id: number;
  payment_number: string;
  business_id: number;
  amount: string;
  currency: string;
  payment_method: string;
  payment_date: string;
  reference_number?: string;
  source: string;
  reconciliation_status: string;
  notes?: string;
  created_at: string;
  allocations: PaymentAllocation[];
}

export interface GenerateInvoiceRequest {
  quotation_id: number;
  version_number?: number;
  due_date?: string;
  notes?: string;
}

export interface RecordPaymentRequest {
  business_id: number;
  amount: string;
  payment_method: string;
  reference_number?: string;
  payment_date?: string;
  notes?: string;
  allocations: {
    invoice_id: number;
    amount: string;
  }[];
}

export interface RecurringBillingResult {
  processed_count: number;
  invoices_generated: number;
  skipped_idempotent: number;
  errors: string[];
}

