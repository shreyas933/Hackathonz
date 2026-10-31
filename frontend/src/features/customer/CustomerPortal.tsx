import React, { useState, useEffect } from 'react';
import { User, CustomerBusiness, CustomerMember, Product, Plan } from '../../types';
import { api } from '../../services/api';
import { Building2, Users, Package, Plus, CheckCircle2, AlertCircle, Shield } from 'lucide-react';

interface CustomerPortalProps {
  user: User;
}

export const CustomerPortal: React.FC<CustomerPortalProps> = ({ user }) => {
  const [activeTab, setActiveTab] = useState<'profile' | 'team' | 'catalog'>('profile');
  const [business, setBusiness] = useState<CustomerBusiness | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Modal state
  const [showMemberModal, setShowMemberModal] = useState(false);
  const [memberForm, setMemberForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'finance_contact' as 'owner' | 'finance_contact' | 'subscription_manager',
  });

  const isOwner = user.role === 'owner';

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [biz, prods, plns] = await Promise.all([
        api.getMyBusiness(),
        api.listProducts(true),
        api.listPlans(undefined, true),
      ]);
      setBusiness(biz);
      setProducts(prods);
      setPlans(plns);
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to load organization data.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.addCustomerMember(memberForm);
      setFeedback({ type: 'success', message: `Team member '${memberForm.full_name}' invited successfully.` });
      setShowMemberModal(false);
      setMemberForm({ full_name: '', email: '', password: '', role: 'finance_contact' });
      loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  if (!business && isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center text-xs text-slate-500">
        Loading organization portal...
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Organization Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-center text-blue-700">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-slate-900">{business?.company_name}</h1>
              <span className="text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded font-medium">
                {business?.status}
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Tax ID: <span className="font-mono text-slate-700">{business?.tax_id || 'Not Specified'}</span> |
              Account Scope: <span className="text-slate-700 font-medium">{business?.billing_country}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <div className="text-right">
            <span className="text-slate-500">Authorized Role</span>
            <div className="font-semibold text-slate-800 capitalize">{user.role.replace('_', ' ')}</div>
          </div>
        </div>
      </div>

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
        <nav className="flex space-x-6">
          <button
            onClick={() => setActiveTab('profile')}
            className={`pb-3 text-xs font-medium border-b-2 transition-colors ${
              activeTab === 'profile' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Organization Profile
          </button>

          <button
            onClick={() => setActiveTab('team')}
            className={`pb-3 text-xs font-medium border-b-2 transition-colors ${
              activeTab === 'team' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Authorized Team Members ({business?.members?.length || 1})
          </button>

          <button
            onClick={() => setActiveTab('catalog')}
            className={`pb-3 text-xs font-medium border-b-2 transition-colors ${
              activeTab === 'catalog' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Available Products & Plans ({products.length})
          </button>
        </nav>
      </div>

      {/* Tab 1: Organization Profile */}
      {activeTab === 'profile' && business && (
        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900 mb-1">Legal and Billing Profile</h2>
          <p className="text-xs text-slate-500 mb-5">
            Details used for invoice generation, tax reporting, and official correspondence.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-slate-50 rounded border border-slate-100">
              <span className="text-slate-500 block mb-1">Company Registered Legal Name</span>
              <span className="font-medium text-slate-800">{business.legal_name || business.company_name}</span>
            </div>

            <div className="p-3 bg-slate-50 rounded border border-slate-100">
              <span className="text-slate-500 block mb-1">Tax Registration / GSTIN</span>
              <span className="font-mono font-medium text-slate-800">{business.tax_id || 'Not on file'}</span>
            </div>

            <div className="p-3 bg-slate-50 rounded border border-slate-100">
              <span className="text-slate-500 block mb-1">Official Billing Email</span>
              <span className="font-medium text-slate-800">{business.contact_email}</span>
            </div>

            <div className="p-3 bg-slate-50 rounded border border-slate-100">
              <span className="text-slate-500 block mb-1">Billing Contact Phone</span>
              <span className="font-medium text-slate-800">{business.contact_phone || 'Not specified'}</span>
            </div>

            <div className="p-3 bg-slate-50 rounded border border-slate-100 md:col-span-2">
              <span className="text-slate-500 block mb-1">Billing Address</span>
              <span className="font-medium text-slate-800">
                {business.billing_address ? (
                  `${business.billing_address}, ${business.billing_city || ''} ${business.billing_state || ''} - ${business.billing_postal_code || ''}, ${business.billing_country}`
                ) : (
                  'No billing address configured.'
                )}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Team Members */}
      {activeTab === 'team' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Authorized Team Members</h2>
              <p className="text-xs text-slate-500">
                Manage individuals authorized to submit subscription requests, view invoices, or administer the account.
              </p>
            </div>
            {isOwner && (
              <button
                onClick={() => setShowMemberModal(true)}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 transition-colors shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Invite Team Member</span>
              </button>
            )}
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Member Name</th>
                  <th className="px-4 py-3">Email Address</th>
                  <th className="px-4 py-3">Customer Role</th>
                  <th className="px-4 py-3">Permissions Scope</th>
                  <th className="px-4 py-3">Added Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {business?.members?.map((mem) => (
                  <tr key={mem.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-slate-900">
                      <div className="flex items-center space-x-2">
                        <span>{mem.full_name}</span>
                        {mem.is_primary && (
                          <span className="text-[10px] bg-slate-100 text-slate-600 border border-slate-200 px-1.5 py-0.2 rounded">Primary</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{mem.email}</td>
                    <td className="px-4 py-3">
                      <span className={`capitalize px-2 py-0.5 rounded text-[11px] font-medium border ${
                        mem.role === 'owner' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                        mem.role === 'finance_contact' ? 'bg-cyan-50 text-cyan-700 border-cyan-200' :
                        'bg-amber-50 text-amber-700 border-amber-200'
                      }`}>
                        {mem.role.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {mem.role === 'owner' && 'Full Business Management'}
                      {mem.role === 'finance_contact' && 'Invoice & Payment Access'}
                      {mem.role === 'subscription_manager' && 'Subscription Requests & Quotes'}
                    </td>
                    <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                      {new Date(mem.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Catalog Browser */}
      {activeTab === 'catalog' && (
        <div className="space-y-6">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Available Products and Subscription Plans</h2>
            <p className="text-xs text-slate-500">
              Transparent tier pricing and terms for Brightloop Software services.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {products.map((prod) => (
              <div key={prod.id} className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[11px] font-mono text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      {prod.code}
                    </span>
                    <h3 className="text-base font-bold text-slate-900 mt-2">{prod.name}</h3>
                    <p className="text-xs text-slate-500 mt-1">{prod.description}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Baseline Rate</span>
                    <div className="text-base font-bold text-slate-900">
                      ₹{parseFloat(prod.sales_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>

                {/* Plans under this product */}
                <div className="border-t border-slate-100 pt-3 space-y-2">
                  <span className="text-xs font-semibold text-slate-700 block">Available Plans:</span>
                  {plans.filter(pl => pl.product_id === prod.id).map(plan => (
                    <div key={plan.id} className="p-3 bg-slate-50 rounded border border-slate-200 flex items-center justify-between text-xs">
                      <div>
                        <div className="font-semibold text-slate-800">{plan.name}</div>
                        <div className="text-[11px] text-slate-500 capitalize">
                          Billed {plan.billing_frequency} • Minimum {plan.min_quantity} seat(s)
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-slate-900">
                          ₹{parseFloat(plan.base_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <span className="text-[10px] text-slate-500">per seat / {plan.billing_frequency}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal: Invite Team Member */}
      {showMemberModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-base font-semibold text-slate-900 mb-1">Add Authorized Team Member</h3>
            <p className="text-xs text-slate-500 mb-4">
              Authorized users can access this business portal per their designated role.
            </p>
            <form onSubmit={handleAddMember} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={memberForm.full_name}
                  onChange={(e) => setMemberForm({ ...memberForm, full_name: e.target.value })}
                  placeholder="e.g. Jane Smith"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Official Email Address *</label>
                <input
                  type="email"
                  required
                  value={memberForm.email}
                  onChange={(e) => setMemberForm({ ...memberForm, email: e.target.value })}
                  placeholder="member@company.com"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Temporary Password *</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={memberForm.password}
                  onChange={(e) => setMemberForm({ ...memberForm, password: e.target.value })}
                  placeholder="Min 8 characters"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Designated Role *</label>
                <select
                  value={memberForm.role}
                  onChange={(e) => setMemberForm({ ...memberForm, role: e.target.value as any })}
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs font-medium"
                >
                  <option value="finance_contact">Finance Contact (Invoices and Payments)</option>
                  <option value="subscription_manager">Subscription Manager (Requests and Quotes)</option>
                  <option value="owner">Co-Owner (Full Business Administration)</option>
                </select>
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowMemberModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
                >
                  Add Member
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

