import {
  User, CustomerBusiness, CustomerMember,
  Product, Plan, TaxRate, DiscountRule, AuditLog,
  SubscriptionRequest, RequestActivity, Quotation, QuotationVersion,
  VersionDiff, Subscription, Invoice, Payment,
  GenerateInvoiceRequest, RecordPaymentRequest, RecurringBillingResult,
  BankFeedItem, BankFeedItemInput, ReminderRule, NotificationLog, RunRemindersResult
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function getToken(): string | null {
  return localStorage.getItem('brightloop_token');
}

export function setToken(token: string) {
  localStorage.setItem('brightloop_token', token);
}

export function clearToken() {
  localStorage.removeItem('brightloop_token');
  localStorage.removeItem('brightloop_user');
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'Request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      // Non-JSON response
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

async function downloadFile(endpoint: string, filename: string): Promise<void> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}${endpoint}`, { headers });
  if (!response.ok) {
    let errorDetail = 'Download failed.';
    try {
      const err = await response.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export const api = {
  // Auth
  async login(payload: { email: string; password: string }) {
    const data = await request<{
      access_token: string;
      token_type: string;
      user_type: string;
      role: string;
      business_id?: number;
      email: string;
      full_name: string;
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    setToken(data.access_token);
    return data;
  },

  async registerCustomer(payload: any) {
    const data = await request<{
      access_token: string;
      token_type: string;
      user_type: string;
      role: string;
      business_id: number;
      email: string;
      full_name: string;
    }>('/auth/register-customer', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    setToken(data.access_token);
    return data;
  },

  async getMe(): Promise<User> {
    return request<User>('/auth/me');
  },

  // Staff (Admin Only)
  async listStaff(): Promise<User[]> {
    return request<User[]>('/admin/staff');
  },

  async createStaff(payload: {
    email: string;
    full_name: string;
    password: string;
    staff_role: 'sales' | 'finance';
    department?: string;
  }): Promise<User> {
    return request<User>('/admin/staff', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateStaffPermissions(staffId: number, payload: any): Promise<User> {
    return request<User>(`/admin/staff/${staffId}/permissions`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  // Customer Portal
  async getMyBusiness(): Promise<CustomerBusiness> {
    return request<CustomerBusiness>('/customer/business');
  },

  async updateMyBusiness(payload: Partial<CustomerBusiness>): Promise<CustomerBusiness> {
    return request<CustomerBusiness>('/customer/business', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  async addCustomerMember(payload: {
    email: string;
    full_name: string;
    password: string;
    role: 'owner' | 'finance_contact' | 'subscription_manager';
  }): Promise<CustomerMember> {
    return request<CustomerMember>('/customer/business/members', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async listAdminBusinesses(): Promise<CustomerBusiness[]> {
    return request<CustomerBusiness[]>('/customer/admin/businesses');
  },

  // Catalog
  async listProducts(activeOnly = false): Promise<Product[]> {
    return request<Product[]>(`/catalog/products?active_only=${activeOnly}`);
  },

  async createProduct(payload: any): Promise<Product> {
    return request<Product>('/catalog/products', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async createVariant(productId: number, payload: any): Promise<any> {
    return request(`/catalog/products/${productId}/variants`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async listPlans(productId?: number, activeOnly = false): Promise<Plan[]> {
    const query = productId ? `?product_id=${productId}&active_only=${activeOnly}` : `?active_only=${activeOnly}`;
    return request<Plan[]>(`/catalog/plans${query}`);
  },

  async createPlan(payload: any): Promise<Plan> {
    return request<Plan>('/catalog/plans', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async listTaxes(activeOnly = false): Promise<TaxRate[]> {
    return request<TaxRate[]>(`/catalog/taxes?active_only=${activeOnly}`);
  },

  async createTax(payload: any): Promise<TaxRate> {
    return request<TaxRate>('/catalog/taxes', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async listDiscounts(activeOnly = false): Promise<DiscountRule[]> {
    return request<DiscountRule[]>(`/catalog/discounts?active_only=${activeOnly}`);
  },

  async createDiscount(payload: any): Promise<DiscountRule> {
    return request<DiscountRule>('/catalog/discounts', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Audit
  async getAuditLogs(limit = 50, offset = 0, action?: string, entityType?: string): Promise<AuditLog[]> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (action) params.append('action', action);
    if (entityType) params.append('entity_type', entityType);
    return request<AuditLog[]>(`/audit/logs?${params.toString()}`);
  },

  // --- Phase 2 Requests ---
  async createCustomerRequest(payload: {
    request_type: string;
    related_subscription_id?: number;
    product_id?: number;
    plan_id?: number;
    variant_id?: number;
    requested_quantity: number;
    notes?: string;
  }): Promise<SubscriptionRequest> {
    return request<SubscriptionRequest>('/customer/requests', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async listCustomerRequests(): Promise<SubscriptionRequest[]> {
    return request<SubscriptionRequest[]>('/customer/requests');
  },

  async getCustomerRequest(requestId: number): Promise<SubscriptionRequest> {
    return request<SubscriptionRequest>(`/customer/requests/${requestId}`);
  },

  async addCustomerRequestActivity(requestId: number, payload: { activity_type: string; message: string }): Promise<RequestActivity> {
    return request<RequestActivity>(`/customer/requests/${requestId}/activity`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async listStaffRequests(typeFilter?: string, statusFilter?: string): Promise<SubscriptionRequest[]> {
    const params = new URLSearchParams();
    if (typeFilter) params.append('request_type', typeFilter);
    if (statusFilter) params.append('status_filter', statusFilter);
    return request<SubscriptionRequest[]>(`/staff/requests?${params.toString()}`);
  },

  async getStaffRequest(requestId: number): Promise<SubscriptionRequest> {
    return request<SubscriptionRequest>(`/staff/requests/${requestId}`);
  },

  async updateStaffRequest(requestId: number, payload: any): Promise<SubscriptionRequest> {
    return request<SubscriptionRequest>(`/staff/requests/${requestId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  async addStaffRequestActivity(requestId: number, payload: { activity_type: string; message: string }): Promise<RequestActivity> {
    return request<RequestActivity>(`/staff/requests/${requestId}/activity`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // --- Phase 2 Quotations ---
  async createStaffQuotation(payload: any, submitForApproval = true): Promise<Quotation> {
    return request<Quotation>(`/staff/quotations?submit_for_approval=${submitForApproval}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async listStaffQuotations(statusFilter?: string): Promise<Quotation[]> {
    const query = statusFilter ? `?status_filter=${statusFilter}` : '';
    return request<Quotation[]>(`/staff/quotations${query}`);
  },

  async getStaffQuotation(quotationId: number): Promise<Quotation> {
    return request<Quotation>(`/staff/quotations/${quotationId}`);
  },

  async reviseQuotation(quotationId: number, payload: any): Promise<QuotationVersion> {
    return request<QuotationVersion>(`/staff/quotations/${quotationId}/versions`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async compareQuotationVersions(quotationId: number, baseVersion: number, targetVersion: number): Promise<VersionDiff> {
    return request<VersionDiff>(`/staff/quotations/${quotationId}/compare?base_version=${baseVersion}&target_version=${targetVersion}`);
  },

  async adminQuotationDecision(quotationId: number, versionNumber: number, payload: { decision_type: string; reason?: string }): Promise<QuotationVersion> {
    return request<QuotationVersion>(`/admin/quotations/${quotationId}/versions/${versionNumber}/decision`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async listCustomerQuotations(): Promise<Quotation[]> {
    return request<Quotation[]>('/customer/quotations');
  },

  async getCustomerQuotation(quotationId: number): Promise<Quotation> {
    return request<Quotation>(`/customer/quotations/${quotationId}`);
  },

  async customerQuotationDecision(quotationId: number, versionNumber: number, payload: { decision_type: string; reason?: string }): Promise<QuotationVersion> {
    return request<QuotationVersion>(`/customer/quotations/${quotationId}/versions/${versionNumber}/decision`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // --- Phase 2 Subscriptions ---
  async listCustomerSubscriptions(): Promise<Subscription[]> {
    return request<Subscription[]>('/customer/subscriptions');
  },

  async getCustomerSubscription(subscriptionId: number): Promise<Subscription> {
    return request<Subscription>(`/customer/subscriptions/${subscriptionId}`);
  },

  async listStaffSubscriptions(statusFilter?: string): Promise<Subscription[]> {
    const query = statusFilter ? `?status_filter=${statusFilter}` : '';
    return request<Subscription[]>(`/staff/subscriptions${query}`);
  },

  async getStaffSubscription(subscriptionId: number): Promise<Subscription> {
    return request<Subscription>(`/staff/subscriptions/${subscriptionId}`);
  },

  async updateSubscriptionStatus(subscriptionId: number, payload: { status: string; reason?: string }): Promise<Subscription> {
    return request<Subscription>(`/staff/subscriptions/${subscriptionId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  // --- Phase 3 Billing & Invoicing ---
  async generateInvoice(payload: GenerateInvoiceRequest): Promise<Invoice> {
    return request<Invoice>('/finance/invoices/generate-from-quotation', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async runRecurringBilling(payload?: { target_date?: string }): Promise<RecurringBillingResult> {
    return request<RecurringBillingResult>('/finance/invoices/run-recurring', {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
  },

  async listFinanceInvoices(params?: { business_id?: number; status_filter?: string; subscription_id?: number }): Promise<Invoice[]> {
    const query = new URLSearchParams();
    if (params?.business_id) query.append('business_id', params.business_id.toString());
    if (params?.status_filter) query.append('status_filter', params.status_filter);
    if (params?.subscription_id) query.append('subscription_id', params.subscription_id.toString());
    const qs = query.toString() ? `?${query.toString()}` : '';
    return request<Invoice[]>(`/finance/invoices${qs}`);
  },

  async getFinanceInvoice(id: number): Promise<Invoice> {
    return request<Invoice>(`/finance/invoices/${id}`);
  },

  async updateInvoiceStatus(id: number, payload: { status: string; notes?: string }): Promise<Invoice> {
    return request<Invoice>(`/finance/invoices/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  async downloadFinanceInvoicePdf(id: number, invoiceNumber: string): Promise<void> {
    return downloadFile(`/finance/invoices/${id}/pdf`, `Invoice-${invoiceNumber}.pdf`);
  },

  // --- Phase 3 Payments & Allocations ---
  async recordPayment(payload: RecordPaymentRequest): Promise<Payment> {
    return request<Payment>('/finance/payments', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async listFinancePayments(params?: { business_id?: number; reconciliation_status?: string }): Promise<Payment[]> {
    const query = new URLSearchParams();
    if (params?.business_id) query.append('business_id', params.business_id.toString());
    if (params?.reconciliation_status) query.append('reconciliation_status', params.reconciliation_status);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return request<Payment[]>(`/finance/payments${qs}`);
  },

  async getFinancePayment(id: number): Promise<Payment> {
    return request<Payment>(`/finance/payments/${id}`);
  },

  // --- Customer Invoices & Payments ---
  async listCustomerInvoices(statusFilter?: string): Promise<Invoice[]> {
    const query = statusFilter ? `?status_filter=${statusFilter}` : '';
    return request<Invoice[]>(`/customer/invoices${query}`);
  },

  async getCustomerInvoice(id: number): Promise<Invoice> {
    return request<Invoice>(`/customer/invoices/${id}`);
  },

  async downloadCustomerInvoicePdf(id: number, invoiceNumber: string): Promise<void> {
    return downloadFile(`/customer/invoices/${id}/pdf`, `Invoice-${invoiceNumber}.pdf`);
  },

  async listCustomerPayments(): Promise<Payment[]> {
    return request<Payment[]>('/customer/payments');
  },

  async getCustomerPayment(id: number): Promise<Payment> {
    return request<Payment>(`/customer/payments/${id}`);
  },

  // --- Quotation PDFs ---
  async downloadStaffQuotationPdf(quotationId: number, versionNumber?: number, quotationNumber?: string): Promise<void> {
    const query = versionNumber ? `?version_number=${versionNumber}` : '';
    const fn = quotationNumber ? `Quotation-${quotationNumber}.pdf` : `Quotation-${quotationId}.pdf`;
    return downloadFile(`/staff/quotations/${quotationId}/pdf${query}`, fn);
  },

  async downloadCustomerQuotationPdf(quotationId: number, versionNumber?: number, quotationNumber?: string): Promise<void> {
    const query = versionNumber ? `?version_number=${versionNumber}` : '';
    const fn = quotationNumber ? `Quotation-${quotationNumber}.pdf` : `Quotation-${quotationId}.pdf`;
    return downloadFile(`/customer/quotations/${quotationId}/pdf${query}`, fn);
  },

  // --- Reconciliation & Bank Feeds ---
  async ingestBankFeed(items: BankFeedItemInput[]): Promise<BankFeedItem[]> {
    return request<BankFeedItem[]>('/finance/reconciliation/feed/ingest', {
      method: 'POST',
      body: JSON.stringify({ items }),
    });
  },

  async listBankFeedItems(status?: string, businessId?: number): Promise<BankFeedItem[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (businessId) params.append('business_id', businessId.toString());
    const query = params.toString() ? `?${params.toString()}` : '';
    return request<BankFeedItem[]>(`/finance/reconciliation/feed${query}`);
  },

  async confirmFeedMatch(itemId: number, invoiceId: number, allocatedAmount?: string, notes?: string): Promise<BankFeedItem> {
    return request<BankFeedItem>(`/finance/reconciliation/feed/${itemId}/match`, {
      method: 'POST',
      body: JSON.stringify({
        invoice_id: invoiceId,
        allocated_amount: allocatedAmount || undefined,
        notes: notes || undefined,
      }),
    });
  },

  async disputeFeedItem(itemId: number, reason: string): Promise<BankFeedItem> {
    return request<BankFeedItem>(`/finance/reconciliation/feed/${itemId}/dispute`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  // --- Reminders & Notifications ---
  async listReminderRules(): Promise<ReminderRule[]> {
    return request<ReminderRule[]>('/reminders/rules');
  },

  async createReminderRule(data: Partial<ReminderRule>): Promise<ReminderRule> {
    return request<ReminderRule>('/reminders/rules', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async runRemindersSweep(targetDate?: string): Promise<RunRemindersResult> {
    return request<RunRemindersResult>('/reminders/run', {
      method: 'POST',
      body: JSON.stringify(targetDate ? { target_date: targetDate } : {}),
    });
  },

  async listReminderHistory(businessId?: number, invoiceId?: number): Promise<NotificationLog[]> {
    const params = new URLSearchParams();
    if (businessId) params.append('business_id', businessId.toString());
    if (invoiceId) params.append('invoice_id', invoiceId.toString());
    const query = params.toString() ? `?${params.toString()}` : '';
    return request<NotificationLog[]>(`/reminders/history${query}`);
  },

  async listCustomerNotifications(unreadOnly?: boolean): Promise<NotificationLog[]> {
    const query = unreadOnly ? '?unread_only=true' : '';
    return request<NotificationLog[]>(`/customer/notifications${query}`);
  },

  async markCustomerNotificationRead(notificationId: number): Promise<NotificationLog> {
    return request<NotificationLog>(`/customer/notifications/${notificationId}/read`, {
      method: 'PATCH',
    });
  },
};
