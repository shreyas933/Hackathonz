import React, { useState, useEffect } from 'react';
import {
  User, CustomerBusiness, CustomerMember, Product, Plan,
  SubscriptionRequest, Quotation, Subscription, Invoice, Payment
} from '../../types';
import { api } from '../../services/api';
import {
  Building2, Users, Package, Plus, CheckCircle2, AlertCircle,
  FileCheck2, Check, X, MessageSquare, Send, Calendar, Clock,
  Download, Receipt, CreditCard
} from 'lucide-react';

interface CustomerPortalProps {
  user: User;
}

export const CustomerPortal: React.FC<CustomerPortalProps> = ({ user }) => {
  const [activeTab, setActiveTab] = useState<
    'subscriptions' | 'invoices' | 'payments' | 'quotations' | 'requests' | 'catalog' | 'team' | 'profile'
  >('subscriptions');

  // Data states
  const [business, setBusiness] = useState<CustomerBusiness | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [requestsList, setRequestsList] = useState<SubscriptionRequest[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // New Request Modal
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [requestForm, setRequestForm] = useState({
    request_type: 'new_subscription',
    requested_quantity: 10,
    product_id: 1,
    plan_id: 1,
    notes: '',
  });

  // Request Activity Modal
  const [selectedRequest, setSelectedRequest] = useState<SubscriptionRequest | null>(null);
  const [replyMessage, setReplyMessage] = useState('');

  // Team Member Modal
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
      const [biz, prods, plns, subs, quotes, reqs, invs, pays] = await Promise.all([
        api.getMyBusiness(),
        api.listProducts(true),
        api.listPlans(undefined, true),
        api.listCustomerSubscriptions(),
        api.listCustomerQuotations(),
        api.listCustomerRequests(),
        api.listCustomerInvoices(),
        api.listCustomerPayments(),
      ]);
      setBusiness(biz);
      setProducts(prods);
      setPlans(plns);
      setSubscriptions(subs);
      setQuotations(quotes);
      setRequestsList(reqs);
      setInvoices(invs);
      setPayments(pays);

      if (prods.length > 0 && plns.length > 0) {
        setRequestForm(prev => ({
          ...prev,
          product_id: prods[0].id,
          plan_id: plns[0].id
        }));
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to load organization data.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createCustomerRequest(requestForm);
      setFeedback({ type: 'success', message: 'Subscription request submitted successfully. Sales will review your requirement.' });
      setShowRequestModal(false);
      setRequestForm(prev => ({ ...prev, notes: '', requested_quantity: 10 }));
      loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleSendReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest || !replyMessage.trim()) return;
    try {
      await api.addCustomerRequestActivity(selectedRequest.id, {
        activity_type: 'customer_response',
        message: replyMessage.trim()
      });
      setReplyMessage('');
      const updated = await api.getCustomerRequest(selectedRequest.id);
      setSelectedRequest(updated);
      setFeedback({ type: 'success', message: 'Response sent to Brightloop Sales.' });
      loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleAcceptQuotation = async (quoteId: number, versionNum: number) => {
    try {
      await api.customerQuotationDecision(quoteId, versionNum, {
        decision_type: 'customer_accepted',
        reason: 'Accepted by authorized customer representative.'
      });
      setFeedback({
        type: 'success',
        message: 'Quotation accepted. Your subscription contract has been confirmed and forwarded to Finance for invoicing.'
      });
      loadData();
      setActiveTab('subscriptions');
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleRejectQuotation = async (quoteId: number, versionNum: number) => {
    const reason = prompt('Please specify reason for rejecting this quotation:');
    if (!reason) return;
    try {
      await api.customerQuotationDecision(quoteId, versionNum, {
        decision_type: 'customer_rejected',
        reason
      });
      setFeedback({ type: 'success', message: 'Quotation rejected. Sales has been notified.' });
      loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleDownloadInvoicePdf = async (invoiceId: number, invoiceNumber: string) => {
    try {
      await api.downloadCustomerInvoicePdf(invoiceId, invoiceNumber);
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Failed to download PDF: ${err.message}` });
    }
  };

  const handleDownloadQuotePdf = async (quotationId: number, versionNumber?: number, quotationNumber?: string) => {
    try {
      await api.downloadCustomerQuotationPdf(quotationId, versionNumber, quotationNumber);
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Failed to download PDF: ${err.message}` });
    }
  };

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
              Tax ID / GSTIN: <span className="font-mono text-slate-700">{business?.tax_id || 'Not Specified'}</span> |
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

      {/* Navigation Tabs */}
      <div className="border-b border-slate-200 mb-6">
        <nav className="flex space-x-6 overflow-x-auto">
          <button
            onClick={() => setActiveTab('subscriptions')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'subscriptions' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            My Subscriptions ({subscriptions.length})
          </button>

          <button
            onClick={() => setActiveTab('invoices')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'invoices' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            My Invoices ({invoices.length})
          </button>

          <button
            onClick={() => setActiveTab('payments')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'payments' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Payment Receipts ({payments.length})
          </button>

          <button
            onClick={() => setActiveTab('quotations')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'quotations' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Quotations & Proposals ({quotations.length})
          </button>

          <button
            onClick={() => setActiveTab('requests')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'requests' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Commercial Requests ({requestsList.length})
          </button>

          <button
            onClick={() => setActiveTab('catalog')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'catalog' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Catalog & Pricing ({products.length})
          </button>

          <button
            onClick={() => setActiveTab('team')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'team' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Team Members ({business?.members?.length || 1})
          </button>

          <button
            onClick={() => setActiveTab('profile')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'profile' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Organization Profile
          </button>
        </nav>
      </div>

      {/* Tab: Subscriptions */}
      {activeTab === 'subscriptions' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Active Subscriptions & Contracts</h2>
              <p className="text-xs text-slate-500">Live service contracts provisioned from accepted commercial quotations.</p>
            </div>
            <button
              onClick={() => setShowRequestModal(true)}
              className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 inline-flex items-center space-x-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Request New Service</span>
            </button>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Contract Ref</th>
                  <th className="px-4 py-3">Seats & Products</th>
                  <th className="px-4 py-3">Recurring Total (₹)</th>
                  <th className="px-4 py-3">Billing Cycle</th>
                  <th className="px-4 py-3">Next Renewal</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {subscriptions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                      You do not have any active subscriptions yet. Review approved proposals in the Quotations tab or submit a New Subscription request.
                    </td>
                  </tr>
                ) : (
                  subscriptions.map((sub) => (
                    <tr key={sub.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-slate-900">{sub.subscription_number}</td>
                      <td className="px-4 py-3">
                        {sub.lines.map(l => (
                          <div key={l.id} className="text-[11px]">
                            {l.quantity} seat(s) • Product #{l.product_id}
                          </div>
                        ))}
                      </td>
                      <td className="px-4 py-3 font-bold text-slate-900">
                        ₹{parseFloat(sub.total_recurring_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 capitalize">{sub.billing_frequency}</td>
                      <td className="px-4 py-3 text-slate-600 font-mono text-[11px]">
                        {sub.next_billing_date ? new Date(sub.next_billing_date).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-medium border capitalize ${
                          sub.status === 'confirmed' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                          sub.status === 'active' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          'bg-slate-100 text-slate-700 border-slate-200'
                        }`}>
                          {sub.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Invoices */}
      {activeTab === 'invoices' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Invoices & Receivables</h2>
            <p className="text-xs text-slate-500">
              Tax invoices issued for your subscription services. Track amount paid, remaining balance due, and download official PDF copies.
            </p>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Total Invoiced</span>
              <div className="text-lg font-bold text-slate-900 mt-1">
                ₹{invoices.reduce((acc, i) => acc + parseFloat(i.final_total || '0'), 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <span className="text-[10px] text-slate-400">{invoices.length} billing statement(s)</span>
            </div>

            <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Total Paid</span>
              <div className="text-lg font-bold text-emerald-700 mt-1">
                ₹{invoices.reduce((acc, i) => acc + parseFloat(i.amount_paid || '0'), 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <span className="text-[10px] text-emerald-600 font-medium">Settled collections</span>
            </div>

            <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Current Balance Due</span>
              <div className="text-lg font-bold text-amber-700 mt-1">
                ₹{invoices.reduce((acc, i) => acc + parseFloat(i.remaining_balance || '0'), 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <span className="text-[10px] text-amber-600 font-medium">Payable balance</span>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Invoice Number</th>
                  <th className="px-4 py-3">Billing Cycle</th>
                  <th className="px-4 py-3">Issue Date</th>
                  <th className="px-4 py-3">Due Date</th>
                  <th className="px-4 py-3">Total (₹)</th>
                  <th className="px-4 py-3">Paid (₹)</th>
                  <th className="px-4 py-3">Balance Due (₹)</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Invoice Copy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {invoices.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-slate-500">
                      No invoices issued yet. When quotations are accepted or recurring renewals execute, invoices will be posted here.
                    </td>
                  </tr>
                ) : (
                  invoices.map((inv) => (
                    <tr key={inv.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-slate-900">{inv.invoice_number}</td>
                      <td className="px-4 py-3 font-mono text-[11px] text-slate-500">{inv.billing_period}</td>
                      <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                        {new Date(inv.issue_date).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                        {new Date(inv.due_date).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 font-bold text-slate-900">
                        ₹{parseFloat(inv.final_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 text-emerald-700 font-medium">
                        ₹{parseFloat(inv.amount_paid).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 font-bold text-amber-800">
                        ₹{parseFloat(inv.remaining_balance).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-medium border capitalize ${
                          inv.status === 'paid' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          inv.status === 'partially_paid' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                          inv.status === 'confirmed' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                          inv.status === 'overdue' ? 'bg-red-50 text-red-700 border-red-200' :
                          'bg-slate-100 text-slate-700 border-slate-200'
                        }`}>
                          {inv.status.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleDownloadInvoicePdf(inv.id, inv.invoice_number)}
                          className="px-2.5 py-1 bg-slate-50 text-slate-700 border border-slate-200 rounded hover:bg-slate-100 text-[11px] font-medium inline-flex items-center space-x-1"
                        >
                          <Download className="w-3 h-3" />
                          <span>PDF</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Payments */}
      {activeTab === 'payments' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Payment Receipts & History</h2>
            <p className="text-xs text-slate-500">
              Receipts and settlements recorded for your business account against subscription invoices.
            </p>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Payment Receipt</th>
                  <th className="px-4 py-3">Payment Date</th>
                  <th className="px-4 py-3">Amount (₹)</th>
                  <th className="px-4 py-3">Method</th>
                  <th className="px-4 py-3">Bank UTR / Ref</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Allocated Invoices</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {payments.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                      No payment receipts posted yet. Payments confirmed by Finance will be listed here.
                    </td>
                  </tr>
                ) : (
                  payments.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-slate-900">{p.payment_number}</td>
                      <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                        {new Date(p.payment_date).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 font-bold text-emerald-700">
                        ₹{parseFloat(p.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 capitalize">{p.payment_method.replace('_', ' ')}</td>
                      <td className="px-4 py-3 font-mono text-[11px] text-slate-600">
                        {p.reference_number || 'N/A'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-medium border capitalize ${
                          p.reconciliation_status === 'reconciled' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          'bg-amber-50 text-amber-700 border-amber-200'
                        }`}>
                          {p.reconciliation_status.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {p.allocations && p.allocations.length > 0 ? (
                          p.allocations.map(a => (
                            <span key={a.id} className="bg-slate-100 text-slate-800 px-1.5 py-0.5 rounded text-[10px] mr-1 border border-slate-200">
                              Inv #{a.invoice_id}: ₹{parseFloat(a.allocated_amount).toLocaleString('en-IN')}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-400 text-[11px]">Direct Payment</span>
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

      {/* Tab: Quotations */}
      {activeTab === 'quotations' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Commercial Quotations</h2>
            <p className="text-xs text-slate-500">
              Approved commercial proposals. Review exact versions and accept to bind your subscription contract.
            </p>
          </div>

          <div className="space-y-4">
            {quotations.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 bg-white border border-slate-200 rounded-lg">
                No quotations submitted yet. When Sales prepares a quotation and Admin approves it, it will appear here.
              </div>
            ) : (
              quotations.map((q) => {
                const latest = q.versions[0];
                if (!latest) return null;
                const isApproved = latest.status === 'approved';
                const isAccepted = latest.status === 'accepted';

                return (
                  <div key={q.id} className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
                    <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-slate-100 pb-3">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-mono font-bold text-slate-900 text-sm">{q.quotation_number}</span>
                          <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[10px] font-mono border">
                            Version {latest.version_number}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Payment terms: <span className="font-medium text-slate-700 capitalize">{latest.payment_terms.replace('_', ' ')}</span> •
                          Valid until: <span className="font-mono text-slate-700">{latest.valid_until ? new Date(latest.valid_until).toLocaleDateString() : '30 days'}</span>
                        </p>
                      </div>

                      <div className="text-right">
                        <span className="text-[11px] text-slate-400">Total Commercial Value</span>
                        <div className="text-lg font-bold text-slate-900">
                          ₹{parseFloat(latest.final_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                      </div>
                    </div>

                    {/* Line Items */}
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-slate-700">Proposal Lines:</span>
                      {latest.lines.map((l) => (
                        <div key={l.id} className="p-3 bg-slate-50 border border-slate-200 rounded text-xs flex justify-between items-center">
                          <div>
                            <span className="font-semibold text-slate-900">{l.description}</span>
                            <div className="text-[11px] text-slate-500">
                              {l.quantity} seat(s) @ ₹{parseFloat(l.unit_price).toFixed(2)}
                              {parseFloat(l.discount_percent) > 0 && ` • Discount: ${parseFloat(l.discount_percent)}% (-₹${parseFloat(l.discount_amount).toFixed(2)})`}
                              {` • Tax: ${parseFloat(l.tax_rate_percent)}% (+₹${parseFloat(l.tax_amount).toFixed(2)})`}
                            </div>
                          </div>
                          <div className="font-bold text-slate-900 text-sm">
                            ₹{parseFloat(l.line_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Actions */}
                    <div className="flex justify-between items-center pt-2">
                      <div>
                        {isAccepted && (
                          <span className="text-emerald-700 font-medium text-xs flex items-center space-x-1">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            <span>Accepted and bound to contract (Immutable).</span>
                          </span>
                        )}
                        {!isApproved && !isAccepted && (
                          <span className="text-slate-500 italic text-xs">
                            Quotation status: {latest.status.replace(/_/g, ' ')}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleDownloadQuotePdf(q.id, latest.version_number, q.quotation_number)}
                          className="px-3 py-1.5 border border-slate-300 text-slate-700 rounded text-xs font-medium hover:bg-slate-50 flex items-center space-x-1"
                          title="Download Quotation PDF"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>PDF</span>
                        </button>
                        {isApproved && (
                          <>
                            <button
                              onClick={() => handleRejectQuotation(q.id, latest.version_number)}
                              className="px-3 py-1.5 border border-red-300 text-red-700 rounded text-xs font-medium hover:bg-red-50 flex items-center space-x-1"
                            >
                              <X className="w-3.5 h-3.5" />
                              <span>Reject</span>
                            </button>
                            <button
                              onClick={() => handleAcceptQuotation(q.id, latest.version_number)}
                              className="px-4 py-1.5 bg-emerald-600 text-white rounded text-xs font-medium hover:bg-emerald-700 shadow-sm flex items-center space-x-1"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>Accept Exact Version {latest.version_number}</span>
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Tab: Requests */}
      {activeTab === 'requests' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Commercial Requests</h2>
              <p className="text-xs text-slate-500">Track seat inquiries and negotiate terms with Brightloop Sales.</p>
            </div>
            <button
              onClick={() => setShowRequestModal(true)}
              className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 inline-flex items-center space-x-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Submit Request</span>
            </button>
          </div>

          <div className="space-y-3">
            {requestsList.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 bg-white border border-slate-200 rounded-lg">
                No requests submitted yet. Click "Submit Request" to begin licensing discussions.
              </div>
            ) : (
              requestsList.map((req) => (
                <div key={req.id} className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-blue-700 text-xs">{req.reference}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium border capitalize ${
                          req.status === 'new' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                          req.status === 'clarification_required' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                          req.status === 'quoted' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                          req.status === 'approved_accepted' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          'bg-slate-100 text-slate-700 border-slate-200'
                        }`}>
                          {req.status.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <h4 className="font-semibold text-slate-900 text-xs mt-1 capitalize">
                        {req.request_type.replace(/_/g, ' ')} • {req.requested_quantity} seat(s)
                      </h4>
                    </div>
                    <button
                      onClick={() => setSelectedRequest(req)}
                      className="px-2.5 py-1 border border-slate-200 rounded text-slate-700 hover:bg-slate-100 text-xs font-medium inline-flex items-center space-x-1"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Activity ({req.activities.length})</span>
                    </button>
                  </div>
                  {req.notes && <p className="text-xs text-slate-600 italic">"{req.notes}"</p>}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Tab: Catalog */}
      {activeTab === 'catalog' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Brightloop Software Catalog</h2>
            <p className="text-xs text-slate-500">Available enterprise products and tiered subscription plans.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {products.map((p) => (
              <div key={p.id} className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm space-y-3">
                <div>
                  <h3 className="font-semibold text-slate-900 text-sm">{p.name}</h3>
                  <span className="font-mono text-[10px] text-slate-400">{p.code}</span>
                  <p className="text-xs text-slate-600 mt-1">{p.description || 'Enterprise SaaS application.'}</p>
                </div>
                <div className="pt-2 border-t border-slate-100 flex justify-between items-center text-xs">
                  <span className="text-slate-500 capitalize">{p.product_type}</span>
                  <span className="font-bold text-slate-900">₹{p.sales_price} list</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Team Members */}
      {activeTab === 'team' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Organization Roster</h2>
              <p className="text-xs text-slate-500">
                Multi-user customer access control. Authorized roles: Business Owner, Finance Contact, and Subscription Manager.
              </p>
            </div>
            {isOwner && (
              <button
                onClick={() => setShowMemberModal(true)}
                className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 inline-flex items-center space-x-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Invite Team Member</span>
              </button>
            )}
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 uppercase font-semibold tracking-wider">
                <tr>
                  <th className="px-4 py-3">Full Name</th>
                  <th className="px-4 py-3">Email Address</th>
                  <th className="px-4 py-3">Tenant Role</th>
                  <th className="px-4 py-3">Account Type</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {business?.members?.map((m) => (
                  <tr key={m.id}>
                    <td className="px-4 py-3 font-medium">{m.full_name}</td>
                    <td className="px-4 py-3 font-mono text-slate-500">{m.email}</td>
                    <td className="px-4 py-3 capitalize">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${
                        m.role === 'owner' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                        m.role === 'finance_contact' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                        'bg-blue-50 text-blue-700 border-blue-200'
                      }`}>
                        {m.role.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500">{m.is_primary ? 'Primary Administrator' : 'Authorized User'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Profile */}
      {activeTab === 'profile' && business && (
        <div className="space-y-4 max-w-xl">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Organization Profile</h2>
            <p className="text-xs text-slate-500">Corporate tax identifier and legal entity address for commercial invoicing.</p>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3 text-xs">
            <div>
              <span className="text-slate-500 block">Company Name:</span>
              <span className="font-semibold text-slate-900 text-sm">{business.company_name}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Tax Identifier / GSTIN:</span>
              <span className="font-mono text-slate-800 font-bold">{business.tax_id || 'Not Provided'}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Billing Address:</span>
              <span className="text-slate-800">{business.billing_address || 'Not Provided'}, {business.billing_city || ''} {business.billing_country}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Billing Contact:</span>
              <span className="text-slate-800">{business.contact_email}</span>
            </div>
          </div>
        </div>
      )}

      {/* Modal: New Subscription Request */}
      {showRequestModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <h3 className="text-sm font-semibold text-slate-900">Request New Subscription</h3>
            <form onSubmit={handleCreateRequest} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Product</label>
                <select
                  value={requestForm.product_id}
                  onChange={(e) => setRequestForm({ ...requestForm, product_id: Number(e.target.value) })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded text-xs"
                >
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Requested Seat Count</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={requestForm.requested_quantity}
                  onChange={(e) => setRequestForm({ ...requestForm, requested_quantity: Number(e.target.value) })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded text-xs font-bold"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Notes / Special Requirements</label>
                <textarea
                  rows={3}
                  value={requestForm.notes}
                  onChange={(e) => setRequestForm({ ...requestForm, notes: e.target.value })}
                  placeholder="Describe your team size or deployment requirements..."
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setShowRequestModal(false)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Cancel</button>
                <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700">Submit Request</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Activity Conversation */}
      {selectedRequest && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <span className="text-xs font-mono text-blue-600 bg-blue-50 px-2 py-0.5 rounded font-bold">
                  {selectedRequest.reference}
                </span>
                <h3 className="text-sm font-semibold text-slate-900 mt-1 capitalize">
                  {selectedRequest.request_type.replace(/_/g, ' ')}: {selectedRequest.requested_quantity} seats
                </h3>
              </div>
              <button onClick={() => setSelectedRequest(null)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {selectedRequest.activities.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-4">No communications recorded on this request.</p>
              ) : (
                selectedRequest.activities.map((act) => (
                  <div
                    key={act.id}
                    className={`p-2.5 rounded text-xs ${
                      act.activity_type.includes('customer')
                        ? 'bg-blue-50 border border-blue-200 text-blue-900'
                        : 'bg-slate-50 border border-slate-200 text-slate-800'
                    }`}
                  >
                    <div className="flex justify-between font-semibold text-[11px] mb-1">
                      <span className="capitalize">{act.activity_type.replace(/_/g, ' ')}</span>
                      <span className="font-mono text-slate-400 font-normal">{new Date(act.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p>{act.message}</p>
                  </div>
                ))
              )}
            </div>

            <form onSubmit={handleSendReply} className="space-y-3 pt-2 border-t border-slate-200">
              <textarea
                rows={2}
                value={replyMessage}
                onChange={(e) => setReplyMessage(e.target.value)}
                placeholder="Reply to Brightloop Sales..."
                required
                className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
              />

              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setSelectedRequest(null)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-xs text-slate-700"
                >
                  Close
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
                >
                  Send Response
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Invite Team Member */}
      {showMemberModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <h3 className="text-sm font-semibold text-slate-900">Invite Team Member</h3>
            <form onSubmit={handleAddMember} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={memberForm.full_name}
                  onChange={(e) => setMemberForm({ ...memberForm, full_name: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-medium mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={memberForm.email}
                  onChange={(e) => setMemberForm({ ...memberForm, email: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-medium mb-1">Temporary Password</label>
                <input
                  type="password"
                  required
                  value={memberForm.password}
                  onChange={(e) => setMemberForm({ ...memberForm, password: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-medium mb-1">Role</label>
                <select
                  value={memberForm.role}
                  onChange={(e) => setMemberForm({ ...memberForm, role: e.target.value as any })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                >
                  <option value="finance_contact">Finance Contact</option>
                  <option value="subscription_manager">Subscription Manager</option>
                  <option value="owner">Business Owner</option>
                </select>
              </div>
              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setShowMemberModal(false)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Cancel</button>
                <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700">Send Invitation</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
