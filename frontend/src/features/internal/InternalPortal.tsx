import React, { useState, useEffect } from 'react';
import { User, Product, Plan, TaxRate, DiscountRule, CustomerBusiness, AuditLog } from '../../types';
import { api } from '../../services/api';
import {
  Layers, Package, Users, Shield, FileText, Plus,
  CheckCircle2, AlertCircle, RefreshCw, Eye, Building2
} from 'lucide-react';

interface InternalPortalProps {
  user: User;
}

export const InternalPortal: React.FC<InternalPortalProps> = ({ user }) => {
  const [activeTab, setActiveTab] = useState<'catalog' | 'plans' | 'taxes_discounts' | 'staff' | 'customers' | 'audit'>('catalog');
  
  // Data state
  const [products, setProducts] = useState<Product[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [taxes, setTaxes] = useState<TaxRate[]>([]);
  const [discounts, setDiscounts] = useState<DiscountRule[]>([]);
  const [staffList, setStaffList] = useState<User[]>([]);
  const [customerBusinesses, setCustomerBusinesses] = useState<CustomerBusiness[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Modals state
  const [showProductModal, setShowProductModal] = useState(false);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [showTaxModal, setShowTaxModal] = useState(false);
  const [showDiscountModal, setShowDiscountModal] = useState(false);
  const [showStaffModal, setShowStaffModal] = useState(false);

  // Form states
  const [productForm, setProductForm] = useState({
    name: '', code: '', product_type: 'saas', sales_price: '', cost_price: '0.00', description: '', notes: ''
  });
  const [planForm, setPlanForm] = useState({
    product_id: 0, name: '', code: '', billing_frequency: 'monthly', base_price: '', min_quantity: 1,
    can_pause: false, can_early_close: true, auto_close_at_end: false, auto_renew: true, trial_days: 0
  });
  const [taxForm, setTaxForm] = useState({ name: '', rate_percent: '', is_compound: false });
  const [discountForm, setDiscountForm] = useState({
    name: '', discount_type: 'percentage', value: '', min_seats: 1, min_amount: '0.00',
    max_allowed_sales_discount: '10.00', requires_admin_approval: false
  });
  const [staffForm, setStaffForm] = useState({
    full_name: '', email: '', password: '', staff_role: 'sales' as 'sales' | 'finance', department: ''
  });

  const isAdmin = user.user_type === 'admin';

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [prods, plns, txs, discs] = await Promise.all([
        api.listProducts(),
        api.listPlans(),
        api.listTaxes(),
        api.listDiscounts(),
      ]);
      setProducts(prods);
      setPlans(plns);
      setTaxes(txs);
      setDiscounts(discs);
      if (prods.length > 0 && planForm.product_id === 0) {
        setPlanForm(prev => ({ ...prev, product_id: prods[0].id }));
      }

      if (isAdmin) {
        const [staff, custs, logs] = await Promise.all([
          api.listStaff(),
          api.listAdminBusinesses(),
          api.getAuditLogs(50),
        ]);
        setStaffList(staff);
        setCustomerBusinesses(custs);
        setAuditLogs(logs);
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to load portal data.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createProduct(productForm);
      setFeedback({ type: 'success', message: `Product '${productForm.name}' created successfully.` });
      setShowProductModal(false);
      setProductForm({ name: '', code: '', product_type: 'saas', sales_price: '', cost_price: '0.00', description: '', notes: '' });
      loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createPlan(planForm);
      setFeedback({ type: 'success', message: `Plan '${planForm.name}' created successfully.` });
      setShowPlanModal(false);
      loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleCreateTax = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createTax(taxForm);
      setFeedback({ type: 'success', message: `Tax rate '${taxForm.name}' added successfully.` });
      setShowTaxModal(false);
      setTaxForm({ name: '', rate_percent: '', is_compound: false });
      loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleCreateDiscount = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createDiscount(discountForm);
      setFeedback({ type: 'success', message: `Discount rule '${discountForm.name}' added successfully.` });
      setShowDiscountModal(false);
      loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleCreateStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createStaff(staffForm);
      setFeedback({ type: 'success', message: `Internal staff account created for '${staffForm.full_name}'.` });
      setShowStaffModal(false);
      setStaffForm({ full_name: '', email: '', password: '', staff_role: 'sales', department: '' });
      loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Role Banner */}
      {!isAdmin && (
        <div className="mb-6 p-3 bg-blue-50 border border-blue-200 rounded-md text-xs text-blue-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-blue-600" />
            <span>
              <strong>Staff Role: {user.role === 'sales' ? 'Sales Representative' : 'Finance Representative'}</strong>.
              Catalog and Staff configuration require Administrator authority. Role-based restrictions are strictly enforced server-side.
            </span>
          </div>
        </div>
      )}

      {feedback && (
        <div className={`mb-6 p-3 rounded-md text-xs flex items-center justify-between ${
          feedback.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          <div className="flex items-center space-x-2">
            {feedback.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <AlertCircle className="w-4 h-4 text-red-600" />}
            <span>{feedback.message}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="font-bold ml-4">✕</button>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200 mb-6">
        <nav className="flex space-x-6 overflow-x-auto">
          <button
            onClick={() => setActiveTab('catalog')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'catalog' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Products & Variants ({products.length})
          </button>

          <button
            onClick={() => setActiveTab('plans')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'plans' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Subscription Plans ({plans.length})
          </button>

          <button
            onClick={() => setActiveTab('taxes_discounts')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'taxes_discounts' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Taxes & Discount Rules
          </button>

          {isAdmin && (
            <>
              <button
                onClick={() => setActiveTab('staff')}
                className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
                  activeTab === 'staff' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Staff Directory ({staffList.length})
              </button>

              <button
                onClick={() => setActiveTab('customers')}
                className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
                  activeTab === 'customers' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Customer Businesses ({customerBusinesses.length})
              </button>

              <button
                onClick={() => setActiveTab('audit')}
                className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
                  activeTab === 'audit' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Audit Trail ({auditLogs.length})
              </button>
            </>
          )}
        </nav>
      </div>

      {/* Tab 1: Products */}
      {activeTab === 'catalog' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Catalog Products</h2>
              <p className="text-xs text-slate-500">Products sold on recurring subscriptions or one-time add-ons.</p>
            </div>
            {isAdmin && (
              <button
                onClick={() => setShowProductModal(true)}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 transition-colors shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create Product</span>
              </button>
            )}
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Product Name</th>
                  <th className="px-4 py-3">Code / SKU</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Base Price (₹)</th>
                  <th className="px-4 py-3">Variants</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {products.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-6 text-center text-slate-500">No products configured yet.</td>
                  </tr>
                ) : (
                  products.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-900">{p.name}</div>
                        {p.description && <div className="text-[11px] text-slate-500">{p.description}</div>}
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-600">{p.code}</td>
                      <td className="px-4 py-3">
                        <span className="capitalize bg-slate-100 px-2 py-0.5 rounded border border-slate-200 text-slate-700 font-mono text-[11px]">
                          {p.product_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium">₹{parseFloat(p.sales_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td className="px-4 py-3">
                        {p.variants && p.variants.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {p.variants.map(v => (
                              <span key={v.id} className="bg-slate-100 text-slate-700 border border-slate-200 text-[11px] px-1.5 py-0.5 rounded">
                                {v.variant_name} (+₹{parseFloat(v.price_adjustment).toFixed(0)})
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-400">None</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {p.is_active ? (
                          <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px] font-medium border border-emerald-200">Active</span>
                        ) : (
                          <span className="text-slate-500 bg-slate-100 px-2 py-0.5 rounded text-[11px] font-medium">Inactive</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Plans */}
      {activeTab === 'plans' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Subscription Plans</h2>
              <p className="text-xs text-slate-500">Defines billing intervals, baseline seat pricing, and lifecycle terms.</p>
            </div>
            {isAdmin && (
              <button
                onClick={() => setShowPlanModal(true)}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 transition-colors shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create Plan</span>
              </button>
            )}
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Plan Name</th>
                  <th className="px-4 py-3">Code</th>
                  <th className="px-4 py-3">Frequency</th>
                  <th className="px-4 py-3">Base Price (₹)</th>
                  <th className="px-4 py-3">Min Seats</th>
                  <th className="px-4 py-3">Lifecycle Policies</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {plans.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-6 text-center text-slate-500">No plans configured yet.</td>
                  </tr>
                ) : (
                  plans.map((pl) => (
                    <tr key={pl.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-medium text-slate-900">{pl.name}</td>
                      <td className="px-4 py-3 font-mono text-slate-600">{pl.code}</td>
                      <td className="px-4 py-3">
                        <span className="capitalize bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-[11px] font-medium border border-blue-200">
                          {pl.billing_frequency}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium">₹{parseFloat(pl.base_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td className="px-4 py-3">{pl.min_quantity}</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1 text-[11px]">
                          {pl.can_pause && <span className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">Pausable</span>}
                          {pl.can_early_close && <span className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">Early Closure</span>}
                          {pl.auto_renew && <span className="bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded">Auto-Renew</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {pl.is_active ? (
                          <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px] font-medium border border-emerald-200">Active</span>
                        ) : (
                          <span className="text-slate-500 bg-slate-100 px-2 py-0.5 rounded text-[11px] font-medium">Inactive</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Taxes & Discounts */}
      {activeTab === 'taxes_discounts' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Taxes */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Tax Configurations</h3>
                <p className="text-[11px] text-slate-500">Applied automatically to quotations and invoices.</p>
              </div>
              {isAdmin && (
                <button
                  onClick={() => setShowTaxModal(true)}
                  className="px-2.5 py-1 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
                >
                  + Add Tax
                </button>
              )}
            </div>

            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-2.5">Tax Name</th>
                    <th className="px-4 py-2.5">Rate (%)</th>
                    <th className="px-4 py-2.5">Type</th>
                    <th className="px-4 py-2.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-800">
                  {taxes.map(t => (
                    <tr key={t.id}>
                      <td className="px-4 py-2.5 font-medium">{t.name}</td>
                      <td className="px-4 py-2.5 font-mono">{parseFloat(t.rate_percent).toFixed(2)}%</td>
                      <td className="px-4 py-2.5 text-slate-500">{t.is_compound ? 'Compound' : 'Standard'}</td>
                      <td className="px-4 py-2.5">
                        <span className="text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded text-[10px] font-medium">Active</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Discounts */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Discount Rules</h3>
                <p className="text-[11px] text-slate-500">Authorized thresholds and admin approval triggers.</p>
              </div>
              {isAdmin && (
                <button
                  onClick={() => setShowDiscountModal(true)}
                  className="px-2.5 py-1 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
                >
                  + Add Rule
                </button>
              )}
            </div>

            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-2.5">Rule Name</th>
                    <th className="px-4 py-2.5">Discount</th>
                    <th className="px-4 py-2.5">Min Seats</th>
                    <th className="px-4 py-2.5">Approval Required</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-800">
                  {discounts.map(d => (
                    <tr key={d.id}>
                      <td className="px-4 py-2.5 font-medium">{d.name}</td>
                      <td className="px-4 py-2.5 font-mono">
                        {d.discount_type === 'percentage' ? `${parseFloat(d.value)}%` : `₹${parseFloat(d.value)}`}
                      </td>
                      <td className="px-4 py-2.5">{d.min_seats} seats</td>
                      <td className="px-4 py-2.5">
                        {d.requires_admin_approval ? (
                          <span className="bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded text-[10px] font-medium">
                            Mandatory Admin Review
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[10px]">Sales Permitted</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Staff Directory (Admin Only) */}
      {isAdmin && activeTab === 'staff' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Internal Staff Accounts</h2>
              <p className="text-xs text-slate-500">Per PRD Section 3.2, only Admin can create and configure staff accounts.</p>
            </div>
            <button
              onClick={() => setShowStaffModal(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 transition-colors shadow-sm"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Staff Account</span>
            </button>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Full Name</th>
                  <th className="px-4 py-3">Work Email</th>
                  <th className="px-4 py-3">Staff Role</th>
                  <th className="px-4 py-3">Department</th>
                  <th className="px-4 py-3">Created Date</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {staffList.map((st) => (
                  <tr key={st.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-slate-900">{st.full_name}</td>
                    <td className="px-4 py-3 text-slate-600">{st.email}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${
                        st.staff_profile?.staff_role === 'sales'
                          ? 'bg-blue-50 text-blue-700 border-blue-200'
                          : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      }`}>
                        {st.staff_profile?.staff_role === 'sales' ? 'Sales Representative' : 'Finance Representative'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500">{st.staff_profile?.department || 'Operations'}</td>
                    <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                      {st.created_at ? new Date(st.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-4 py-3">
                      {st.is_active ? (
                        <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px] font-medium border border-emerald-200">Active</span>
                      ) : (
                        <span className="text-red-700 bg-red-50 px-2 py-0.5 rounded text-[11px] font-medium border border-red-200">Inactive</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 5: Customer Businesses (Admin Only) */}
      {isAdmin && activeTab === 'customers' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Customer Organizations</h2>
            <p className="text-xs text-slate-500">Registered businesses and authorized customer representatives.</p>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Company Name</th>
                  <th className="px-4 py-3">Tax ID / GSTIN</th>
                  <th className="px-4 py-3">Primary Contact</th>
                  <th className="px-4 py-3">Location</th>
                  <th className="px-4 py-3">Authorized Users</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {customerBusinesses.map(biz => (
                  <tr key={biz.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-900">{biz.company_name}</div>
                      <div className="text-[11px] text-slate-500">{biz.legal_name}</div>
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-600">{biz.tax_id || 'Not Specified'}</td>
                    <td className="px-4 py-3">
                      <div>{biz.contact_email}</div>
                      {biz.contact_phone && <div className="text-[11px] text-slate-500">{biz.contact_phone}</div>}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {biz.billing_city ? `${biz.billing_city}, ${biz.billing_country}` : biz.billing_country}
                    </td>
                    <td className="px-4 py-3">
                      <span className="bg-purple-50 text-purple-700 px-2 py-0.5 rounded text-[11px] font-medium border border-purple-200">
                        {biz.members?.length || 1} team member(s)
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px] font-medium border border-emerald-200">
                        {biz.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 6: Audit Trail (Admin Only) */}
      {isAdmin && activeTab === 'audit' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">System Audit Trail</h2>
            <p className="text-xs text-slate-500">Append-only compliance log for commercial and financial actions (PRD FR-AUD-1).</p>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Timestamp (UTC)</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Entity</th>
                  <th className="px-4 py-3">Actor Email</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">State / Payload</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800 font-mono text-[11px]">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-2.5 text-slate-500 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-2.5 font-bold text-slate-800">{log.action}</td>
                    <td className="px-4 py-2.5 text-slate-600">
                      {log.entity_type} {log.entity_id ? `(#${log.entity_id})` : ''}
                    </td>
                    <td className="px-4 py-2.5 text-slate-700 font-sans">{log.actor_email || 'System'}</td>
                    <td className="px-4 py-2.5 capitalize">{log.actor_role || 'system'}</td>
                    <td className="px-4 py-2.5 text-slate-600 truncate max-w-xs font-sans">
                      {log.after_state || log.before_state || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal: Create Product */}
      {showProductModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-base font-semibold text-slate-900 mb-4">Create Catalog Product</h3>
            <form onSubmit={handleCreateProduct} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Product Name *</label>
                <input
                  type="text"
                  required
                  value={productForm.name}
                  onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                  placeholder="e.g. Cloud ERP Suite"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Unique Code *</label>
                <input
                  type="text"
                  required
                  value={productForm.code}
                  onChange={(e) => setProductForm({ ...productForm, code: e.target.value })}
                  placeholder="e.g. BL-ERP"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Type</label>
                  <select
                    value={productForm.product_type}
                    onChange={(e) => setProductForm({ ...productForm, product_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  >
                    <option value="saas">SaaS Core</option>
                    <option value="addon">Addon Module</option>
                    <option value="service">Implementation Service</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Base Sales Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={productForm.sales_price}
                    onChange={(e) => setProductForm({ ...productForm, sales_price: e.target.value })}
                    placeholder="1500.00"
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Description</label>
                <textarea
                  rows={2}
                  value={productForm.description}
                  onChange={(e) => setProductForm({ ...productForm, description: e.target.value })}
                  placeholder="Commercial product description"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowProductModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
                >
                  Save Product
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Create Plan */}
      {showPlanModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-base font-semibold text-slate-900 mb-4">Create Subscription Plan</h3>
            <form onSubmit={handleCreatePlan} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Parent Product *</label>
                  <select
                    value={planForm.product_id}
                    onChange={(e) => setPlanForm({ ...planForm, product_id: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  >
                    {products.map(p => (
                      <option key={p.id} value={p.id}>{p.name} ({p.code})</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Plan Name *</label>
                  <input
                    type="text"
                    required
                    value={planForm.name}
                    onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })}
                    placeholder="e.g. Standard Yearly"
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Plan Code *</label>
                  <input
                    type="text"
                    required
                    value={planForm.code}
                    onChange={(e) => setPlanForm({ ...planForm, code: e.target.value })}
                    placeholder="PLAN-STD-Y"
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  />
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Billing Frequency *</label>
                  <select
                    value={planForm.billing_frequency}
                    onChange={(e) => setPlanForm({ ...planForm, billing_frequency: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Base Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={planForm.base_price}
                    onChange={(e) => setPlanForm({ ...planForm, base_price: e.target.value })}
                    placeholder="15000.00"
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  />
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100">
                <span className="block text-slate-700 font-medium mb-2">Lifecycle Options (PRD FR-CAT-3)</span>
                <div className="grid grid-cols-2 gap-2">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={planForm.can_pause}
                      onChange={(e) => setPlanForm({ ...planForm, can_pause: e.target.checked })}
                      className="rounded text-blue-600"
                    />
                    <span>Allow Subscription Pause</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={planForm.can_early_close}
                      onChange={(e) => setPlanForm({ ...planForm, can_early_close: e.target.checked })}
                      className="rounded text-blue-600"
                    />
                    <span>Allow Early Closure</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={planForm.auto_renew}
                      onChange={(e) => setPlanForm({ ...planForm, auto_renew: e.target.checked })}
                      className="rounded text-blue-600"
                    />
                    <span>Default Auto-Renewal</span>
                  </label>
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowPlanModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
                >
                  Save Plan
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Create Tax */}
      {showTaxModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-sm w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-base font-semibold text-slate-900 mb-4">Add Tax Rate</h3>
            <form onSubmit={handleCreateTax} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Tax Label *</label>
                <input
                  type="text"
                  required
                  value={taxForm.name}
                  onChange={(e) => setTaxForm({ ...taxForm, name: e.target.value })}
                  placeholder="e.g. GST 18%"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Rate Percent (%) *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={taxForm.rate_percent}
                  onChange={(e) => setTaxForm({ ...taxForm, rate_percent: e.target.value })}
                  placeholder="18.00"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowTaxModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
                >
                  Save Tax Rate
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Create Discount Rule */}
      {showDiscountModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-base font-semibold text-slate-900 mb-4">Add Discount Rule</h3>
            <form onSubmit={handleCreateDiscount} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Rule Name *</label>
                <input
                  type="text"
                  required
                  value={discountForm.name}
                  onChange={(e) => setDiscountForm({ ...discountForm, name: e.target.value })}
                  placeholder="e.g. Enterprise Tier Discount"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Discount Type</label>
                  <select
                    value={discountForm.discount_type}
                    onChange={(e) => setDiscountForm({ ...discountForm, discount_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  >
                    <option value="percentage">Percentage (%)</option>
                    <option value="fixed_amount">Fixed Amount (₹)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Value *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={discountForm.value}
                    onChange={(e) => setDiscountForm({ ...discountForm, value: e.target.value })}
                    placeholder="15.00"
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Min Seats</label>
                  <input
                    type="number"
                    value={discountForm.min_seats}
                    onChange={(e) => setDiscountForm({ ...discountForm, min_seats: parseInt(e.target.value) || 1 })}
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  />
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Sales Limit (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={discountForm.max_allowed_sales_discount}
                    onChange={(e) => setDiscountForm({ ...discountForm, max_allowed_sales_discount: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  />
                </div>
              </div>

              <label className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  checked={discountForm.requires_admin_approval}
                  onChange={(e) => setDiscountForm({ ...discountForm, requires_admin_approval: e.target.checked })}
                  className="rounded text-blue-600"
                />
                <span className="text-slate-700 font-medium">Requires Mandatory Admin Approval</span>
              </label>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowDiscountModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
                >
                  Save Discount Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Create Staff Account */}
      {showStaffModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-base font-semibold text-slate-900 mb-1">Create Internal Staff Account</h3>
            <p className="text-xs text-slate-500 mb-4">Only Administrator can provision internal staff profiles.</p>
            <form onSubmit={handleCreateStaff} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={staffForm.full_name}
                  onChange={(e) => setStaffForm({ ...staffForm, full_name: e.target.value })}
                  placeholder="e.g. John Doe"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Company Email *</label>
                <input
                  type="email"
                  required
                  value={staffForm.email}
                  onChange={(e) => setStaffForm({ ...staffForm, email: e.target.value })}
                  placeholder="staff@brightloop.com"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Initial Password *</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={staffForm.password}
                  onChange={(e) => setStaffForm({ ...staffForm, password: e.target.value })}
                  placeholder="Min 8 characters"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Role Assignment *</label>
                  <select
                    value={staffForm.staff_role}
                    onChange={(e) => setStaffForm({ ...staffForm, staff_role: e.target.value as 'sales' | 'finance' })}
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs font-medium"
                  >
                    <option value="sales">Sales Representative</option>
                    <option value="finance">Finance Representative</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Department</label>
                  <input
                    type="text"
                    value={staffForm.department}
                    onChange={(e) => setStaffForm({ ...staffForm, department: e.target.value })}
                    placeholder="e.g. Mid-Market"
                    className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowStaffModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
                >
                  Create Staff
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

