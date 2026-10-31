import {
  User, CustomerBusiness, CustomerMember,
  Product, Plan, TaxRate, DiscountRule, AuditLog
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
};

