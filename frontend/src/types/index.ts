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

