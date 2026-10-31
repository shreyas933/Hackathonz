import React, { useState, useEffect } from 'react';
import {
  User, Product, Plan, TaxRate, DiscountRule, CustomerBusiness, AuditLog,
  SubscriptionRequest, Quotation, QuotationVersion, VersionDiff, Subscription,
  Invoice, Payment, BankFeedItem, BankFeedItemInput, ReminderRule, NotificationLog, RunRemindersResult
} from '../../types';
import { api } from '../../services/api';
import {
  Layers, Package, Users, Shield, FileText, Plus,
  CheckCircle2, AlertCircle, RefreshCw, Eye, Building2,
  FileCheck2, GitCompare, MessageSquare, Clock, Send, Ban,
  Receipt, CreditCard, Download, Play, DollarSign,
  GitMerge, Bell, Sliders, Search, AlertTriangle
} from 'lucide-react';

interface InternalPortalProps {
  user: User;
}

export const InternalPortal: React.FC<InternalPortalProps> = ({ user }) => {
  const [activeTab, setActiveTab] = useState<
    'requests' | 'quotations' | 'approval_queue' | 'subscriptions' | 'invoices' | 'payments' | 'reconciliation' | 'reminders' | 'catalog' | 'plans' | 'taxes_discounts' | 'staff' | 'customers' | 'audit'
  >('requests');

  // Data states
  const [requestsList, setRequestsList] = useState<SubscriptionRequest[]>([]);
  const [feedItems, setFeedItems] = useState<BankFeedItem[]>([]);
  const [reminderRules, setReminderRules] = useState<ReminderRule[]>([]);
  const [reminderHistory, setReminderHistory] = useState<NotificationLog[]>([]);

  // Phase 4 Automation & Reconciliation states
  const [feedFilterStatus, setFeedFilterStatus] = useState<string>('all');
  const [showIngestModal, setShowIngestModal] = useState<boolean>(false);
  const [ingestForm, setIngestForm] = useState({
    transaction_id: '',
    amount: '',
    currency: 'INR',
    raw_narration: '',
    sender_name: '',
    bank_account_number: 'HDFC-00998811',
  });
  const [confirmMatchModal, setConfirmMatchModal] = useState<{
    item: BankFeedItem;
    invoice_id: number;
    amount: string;
    notes: string;
  } | null>(null);
  const [disputeModal, setDisputeModal] = useState<{
    item: BankFeedItem;
    reason: string;
  } | null>(null);

  const [showRuleModal, setShowRuleModal] = useState<boolean>(false);
  const [ruleForm, setRuleForm] = useState({
    name: '',
    trigger_type: 'before_due' as 'before_due' | 'on_due' | 'after_due_overdue' | 'upcoming_renewal',
    days_offset: -3,
    channel: 'email' as 'email' | 'in_app',
    subject_template: 'Reminder: Invoice {invoice_number} is due soon',
    body_template: 'Dear Customer, this is a reminder that invoice {invoice_number} is due on {due_date}. Remaining balance: {amount_due}.',
    escalation_level: 'standard' as 'standard' | 'urgent' | 'final_notice',
  });

  const [showSweepModal, setShowSweepModal] = useState<boolean>(false);
  const [sweepTargetDate, setSweepTargetDate] = useState<string>('');
  const [sweepResult, setSweepResult] = useState<RunRemindersResult | null>(null);
  const [quotationsList, setQuotationsList] = useState<Quotation[]>([]);
  const [subscriptionsList, setSubscriptionsList] = useState<Subscription[]>([]);
  const [invoicesList, setInvoicesList] = useState<Invoice[]>([]);
  const [paymentsList, setPaymentsList] = useState<Payment[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [taxes, setTaxes] = useState<TaxRate[]>([]);
  const [discounts, setDiscounts] = useState<DiscountRule[]>([]);
  const [staffList, setStaffList] = useState<User[]>([]);
  const [customerBusinesses, setCustomerBusinesses] = useState<CustomerBusiness[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Selected item modals
  const [selectedRequest, setSelectedRequest] = useState<SubscriptionRequest | null>(null);
  const [requestActivityMsg, setRequestActivityMsg] = useState('');
  const [activityType, setActivityType] = useState<'sales_note' | 'clarification_request'>('sales_note');

  // Quotation modals
  const [showCreateQuoteModal, setShowCreateQuoteModal] = useState(false);
  const [quoteForm, setQuoteForm] = useState({
    business_id: 1,
    request_id: undefined as number | undefined,
    payment_terms: 'net_30',
    validity_days: 30,
    lines: [
      { product_id: 1, plan_id: 1, quantity: 20, unit_price: '1500.00', discount_percent: '0.00', tax_rate_percent: '18.00' }
    ]
  });

  const [selectedQuotation, setSelectedQuotation] = useState<Quotation | null>(null);
  const [showReviseModal, setShowReviseModal] = useState(false);
  const [reviseForm, setReviseForm] = useState({
    revision_reason: '',
    payment_terms: 'net_30',
    validity_days: 30,
    lines: [
      { product_id: 1, plan_id: 1, quantity: 25, unit_price: '1500.00', discount_percent: '5.00', tax_rate_percent: '18.00' }
    ]
  });

  // Version diff modal
  const [diffModal, setDiffModal] = useState<{ quoteId: number; base: number; target: number; diff: VersionDiff | null } | null>(null);

  // Admin decision modal
  const [adminDecisionModal, setAdminDecisionModal] = useState<{
    quoteId: number;
    versionNumber: number;
    decisionType: 'admin_approved' | 'admin_rejected' | 'admin_changes_requested';
    reason: string;
  } | null>(null);

  // Phase 3 Invoicing & Payments Modals
  const [generateInvoiceModal, setGenerateInvoiceModal] = useState<{
    quoteId: number;
    quoteNumber: string;
    versionNumber: number;
  } | null>(null);
  const [invoiceDueDate, setInvoiceDueDate] = useState<string>('');

  const [recurringModal, setRecurringModal] = useState<boolean>(false);
  const [recurringTargetDate, setRecurringTargetDate] = useState<string>('');

  const [showRecordPaymentModal, setShowRecordPaymentModal] = useState<boolean>(false);
  const [paymentForm, setPaymentForm] = useState({
    business_id: 1,
    amount: '',
    payment_method: 'bank_transfer',
    reference_number: '',
    notes: '',
    selected_invoice_id: 0,
  });

  // Catalog modals
  const [showProductModal, setShowProductModal] = useState(false);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [showTaxModal, setShowTaxModal] = useState(false);
  const [showDiscountModal, setShowDiscountModal] = useState(false);
  const [showStaffModal, setShowStaffModal] = useState(false);

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
  const isSales = user.role === 'sales';
  const isFinance = user.role === 'finance';

  const loadAllData = async () => {
    setIsLoading(true);
    try {
      const [reqs, quotes, subs, prods, plns, txs, discs, invs, pays, bizs, feeds, rules, notifs] = await Promise.all([
        api.listStaffRequests(),
        api.listStaffQuotations(),
        api.listStaffSubscriptions(),
        api.listProducts(),
        api.listPlans(),
        api.listTaxes(),
        api.listDiscounts(),
        api.listFinanceInvoices(),
        api.listFinancePayments(),
        api.listAdminBusinesses(),
        api.listBankFeedItems(),
        api.listReminderRules(),
        api.listReminderHistory(),
      ]);
      setRequestsList(reqs);
      setQuotationsList(quotes);
      setSubscriptionsList(subs);
      setProducts(prods);
      setPlans(plns);
      setTaxes(txs);
      setDiscounts(discs);
      setInvoicesList(invs);
      setPaymentsList(pays);
      setCustomerBusinesses(bizs);
      setFeedItems(feeds);
      setReminderRules(rules);
      setReminderHistory(notifs);

      if (prods.length > 0 && plns.length > 0) {
        setQuoteForm(prev => ({
          ...prev,
          lines: [{
            product_id: prods[0].id,
            plan_id: plns[0].id,
            quantity: 20,
            unit_price: String(plns[0].base_price),
            discount_percent: '0.00',
            tax_rate_percent: '18.00'
          }]
        }));
      }

      if (isAdmin) {
        const [staff, logs] = await Promise.all([
          api.listStaff(),
          api.getAuditLogs(50),
        ]);
        setStaffList(staff);
        setAuditLogs(logs);
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to load data.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  // Commercial Action Handlers
  const handleAddRequestActivity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest || !requestActivityMsg.trim()) return;
    try {
      const act = await api.addStaffRequestActivity(selectedRequest.id, {
        message: requestActivityMsg,
        activity_type: activityType,
      });
      setSelectedRequest({
        ...selectedRequest,
        activities: [...selectedRequest.activities, act],
        status: activityType === 'clarification_request' ? 'clarification_required' : selectedRequest.status
      });
      setRequestActivityMsg('');
      setFeedback({ type: 'success', message: 'Activity note added to request history.' });
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleCreateQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const newQuote = await api.createStaffQuotation({
        business_id: quoteForm.business_id,
        request_id: quoteForm.request_id,
        payment_terms: quoteForm.payment_terms,
        validity_days: Number(quoteForm.validity_days),
        lines: quoteForm.lines.map(l => ({
          product_id: Number(l.product_id),
          plan_id: Number(l.plan_id),
          quantity: Number(l.quantity),
          unit_price: l.unit_price,
          discount_percent: l.discount_percent,
          tax_rate_percent: l.tax_rate_percent,
        }))
      }, true);
      setFeedback({ type: 'success', message: `Quotation ${newQuote.quotation_number} created and submitted for mandatory Admin approval.` });
      setShowCreateQuoteModal(false);
      loadAllData();
      setActiveTab('quotations');
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleReviseQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedQuotation) return;
    try {
      const revisedVer = await api.reviseQuotation(selectedQuotation.id, {
        revision_reason: reviseForm.revision_reason,
        payment_terms: reviseForm.payment_terms,
        validity_days: Number(reviseForm.validity_days),
        lines: reviseForm.lines.map(l => ({
          product_id: Number(l.product_id),
          plan_id: Number(l.plan_id),
          quantity: Number(l.quantity),
          unit_price: l.unit_price,
          discount_percent: l.discount_percent,
          tax_rate_percent: l.tax_rate_percent,
        }))
      });
      setFeedback({ type: 'success', message: `Quotation version ${revisedVer.version_number} submitted for Admin approval.` });
      setShowReviseModal(false);
      setSelectedQuotation(null);
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleOpenDiff = async (quoteId: number, base: number, target: number) => {
    try {
      const diff = await api.compareQuotationVersions(quoteId, base, target);
      setDiffModal({ quoteId, base, target, diff });
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleAdminDecision = async () => {
    if (!adminDecisionModal) return;
    try {
      await api.adminQuotationDecision(
        adminDecisionModal.quoteId,
        adminDecisionModal.versionNumber,
        {
          decision_type: adminDecisionModal.decisionType,
          reason: adminDecisionModal.reason || undefined,
        }
      );
      setFeedback({
        type: 'success',
        message: `Quotation #${adminDecisionModal.quoteId} v${adminDecisionModal.versionNumber}: decision processed (${adminDecisionModal.decisionType.replace('admin_', '')}).`
      });
      setAdminDecisionModal(null);
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleToggleSubStatus = async (subId: number, currentStatus: string) => {
    const nextStatus = currentStatus === 'active' ? 'paused' : 'active';
    try {
      await api.updateSubscriptionStatus(subId, { status: nextStatus, reason: `Status changed by ${user.full_name}` });
      setFeedback({ type: 'success', message: `Subscription status updated to ${nextStatus}.` });
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleGenerateInvoice = async () => {
    if (!generateInvoiceModal) return;
    try {
      const inv = await api.generateInvoice({
        quotation_id: generateInvoiceModal.quoteId,
        version_number: generateInvoiceModal.versionNumber,
        due_date: invoiceDueDate ? new Date(invoiceDueDate).toISOString() : undefined,
      });
      setFeedback({
        type: 'success',
        message: `Invoice ${inv.invoice_number} generated successfully for ₹${parseFloat(inv.final_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}.`
      });
      setGenerateInvoiceModal(null);
      setInvoiceDueDate('');
      loadAllData();
      setActiveTab('invoices');
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleRunRecurring = async () => {
    try {
      const res = await api.runRecurringBilling(
        recurringTargetDate ? { target_date: new Date(recurringTargetDate).toISOString() } : undefined
      );
      setFeedback({
        type: 'success',
        message: `Recurring billing completed: ${res.invoices_generated} invoices generated, ${res.skipped_idempotent} skipped idempotently (${res.processed_count} subscriptions checked).`
      });
      setRecurringModal(false);
      setRecurringTargetDate('');
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!paymentForm.amount || parseFloat(paymentForm.amount) <= 0) {
      setFeedback({ type: 'error', message: 'Valid payment amount is required.' });
      return;
    }
    try {
      const allocations = paymentForm.selected_invoice_id > 0
        ? [{ invoice_id: paymentForm.selected_invoice_id, amount: paymentForm.amount }]
        : [];
      const payment = await api.recordPayment({
        business_id: paymentForm.business_id,
        amount: paymentForm.amount,
        payment_method: paymentForm.payment_method,
        reference_number: paymentForm.reference_number || undefined,
        notes: paymentForm.notes || undefined,
        allocations,
      });
      setFeedback({
        type: 'success',
        message: `Payment ${payment.payment_number} recorded (Status: ${payment.reconciliation_status}).`
      });
      setShowRecordPaymentModal(false);
      setPaymentForm({
        business_id: customerBusinesses[0]?.id || 1,
        amount: '',
        payment_method: 'bank_transfer',
        reference_number: '',
        notes: '',
        selected_invoice_id: 0,
      });
      loadAllData();
      setActiveTab('payments');
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleDownloadInvoicePdf = async (invoiceId: number, invoiceNumber: string) => {
    try {
      await api.downloadFinanceInvoicePdf(invoiceId, invoiceNumber);
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Failed to download PDF: ${err.message}` });
    }
  };

  const handleDownloadQuotePdf = async (quotationId: number, versionNumber?: number, quotationNumber?: string) => {
    try {
      await api.downloadStaffQuotationPdf(quotationId, versionNumber, quotationNumber);
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Failed to download PDF: ${err.message}` });
    }
  };

  const handleUpdateInvoiceStatus = async (invoiceId: number, newStatus: string) => {
    try {
      await api.updateInvoiceStatus(invoiceId, { status: newStatus });
      setFeedback({ type: 'success', message: `Invoice status updated to ${newStatus}.` });
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  // Catalog Form Handlers
  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createProduct(productForm);
      setFeedback({ type: 'success', message: 'Product created successfully.' });
      setShowProductModal(false);
      setProductForm({ name: '', code: '', product_type: 'saas', sales_price: '', cost_price: '0.00', description: '', notes: '' });
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createPlan(planForm);
      setFeedback({ type: 'success', message: 'Subscription plan created successfully.' });
      setShowPlanModal(false);
      setPlanForm({
        product_id: products[0]?.id || 0, name: '', code: '', billing_frequency: 'monthly', base_price: '', min_quantity: 1,
        can_pause: false, can_early_close: true, auto_close_at_end: false, auto_renew: true, trial_days: 0
      });
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleCreateTax = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createTax(taxForm);
      setFeedback({ type: 'success', message: 'Tax rate created successfully.' });
      setShowTaxModal(false);
      setTaxForm({ name: '', rate_percent: '', is_compound: false });
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleCreateDiscount = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createDiscount(discountForm);
      setFeedback({ type: 'success', message: 'Discount rule created successfully.' });
      setShowDiscountModal(false);
      setDiscountForm({
        name: '', discount_type: 'percentage', value: '', min_seats: 1, min_amount: '0.00',
        max_allowed_sales_discount: '10.00', requires_admin_approval: false
      });
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleCreateStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createStaff(staffForm);
      setFeedback({ type: 'success', message: 'Staff user profile created successfully.' });
      setShowStaffModal(false);
      setStaffForm({ full_name: '', email: '', password: '', staff_role: 'sales', department: '' });
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  // --- Phase 4 Reconciliation & Reminders Handlers ---
  const handleIngestBankFeed = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const txId = ingestForm.transaction_id || `TX-${Date.now().toString().slice(-6)}`;
      await api.ingestBankFeed([{
        transaction_id: txId,
        amount: ingestForm.amount,
        currency: ingestForm.currency,
        raw_narration: ingestForm.raw_narration,
        sender_name: ingestForm.sender_name || undefined,
        bank_account_number: ingestForm.bank_account_number || undefined,
      }]);
      setFeedback({ type: 'success', message: `Bank feed item ${txId} ingested and evaluated.` });
      setShowIngestModal(false);
      setIngestForm({
        transaction_id: '',
        amount: '',
        currency: 'INR',
        raw_narration: '',
        sender_name: '',
        bank_account_number: 'HDFC-00998811',
      });
      loadAllData();
      setActiveTab('reconciliation');
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleConfirmMatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!confirmMatchModal) return;
    try {
      await api.confirmFeedMatch(
        confirmMatchModal.item.id,
        confirmMatchModal.invoice_id,
        confirmMatchModal.amount || undefined,
        confirmMatchModal.notes || undefined
      );
      setFeedback({ type: 'success', message: `Transaction ${confirmMatchModal.item.transaction_id} reconciled successfully.` });
      setConfirmMatchModal(null);
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleDispute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!disputeModal) return;
    try {
      await api.disputeFeedItem(disputeModal.item.id, disputeModal.reason);
      setFeedback({ type: 'success', message: 'Transaction marked as disputed.' });
      setDisputeModal(null);
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleCreateReminderRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createReminderRule(ruleForm);
      setFeedback({ type: 'success', message: 'Reminder governance rule configured.' });
      setShowRuleModal(false);
      setRuleForm({
        name: '',
        trigger_type: 'before_due',
        days_offset: -3,
        channel: 'email',
        subject_template: 'Reminder: Invoice {invoice_number} is due soon',
        body_template: 'Dear Customer, this is a reminder that invoice {invoice_number} is due on {due_date}. Remaining balance: {amount_due}.',
        escalation_level: 'standard',
      });
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleRunSweep = async () => {
    try {
      const res = await api.runRemindersSweep(sweepTargetDate || undefined);
      setSweepResult(res);
      setFeedback({
        type: 'success',
        message: `Reminder sweep complete: ${res.reminders_sent} reminder(s) sent, ${res.skipped_count} skipped.`
      });
      loadAllData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const pendingApprovalQuotes = quotationsList.filter(q => q.status === 'submitted_for_approval');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Role Banner */}
      <div className="mb-6 p-3 bg-white border border-slate-200 rounded-md text-xs text-slate-700 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-2">
          <Shield className="w-4 h-4 text-blue-600" />
          <span>
            Logged in as <strong>{user.full_name}</strong> ({user.role === 'admin' ? 'Administrator' : user.role === 'sales' ? 'Sales Representative' : 'Finance Representative'}).
            Commercial workflow: Request → Quotation → Mandatory Admin Approval → Customer Acceptance → Billing & Invoicing.
          </span>
        </div>
        <button onClick={loadAllData} className="inline-flex items-center space-x-1 text-slate-500 hover:text-slate-800">
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
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
        <nav className="flex space-x-6 overflow-x-auto">
          <button
            onClick={() => setActiveTab('requests')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'requests' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Subscription Requests ({requestsList.length})
          </button>

          <button
            onClick={() => setActiveTab('quotations')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'quotations' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Quotations & Versioning ({quotationsList.length})
          </button>

          {isAdmin && (
            <button
              onClick={() => setActiveTab('approval_queue')}
              className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors flex items-center space-x-1.5 ${
                activeTab === 'approval_queue' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <span>Admin Approval Queue</span>
              {pendingApprovalQuotes.length > 0 && (
                <span className="bg-amber-100 text-amber-800 text-[10px] px-1.5 py-0.2 rounded-full font-bold">
                  {pendingApprovalQuotes.length}
                </span>
              )}
            </button>
          )}

          <button
            onClick={() => setActiveTab('subscriptions')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'subscriptions' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Subscriptions ({subscriptionsList.length})
          </button>

          <button
            onClick={() => setActiveTab('invoices')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'invoices' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Invoices ({invoicesList.length})
          </button>

          <button
            onClick={() => setActiveTab('payments')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'payments' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Payments ({paymentsList.length})
          </button>

          <button
            onClick={() => setActiveTab('reconciliation')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors flex items-center space-x-1.5 ${
              activeTab === 'reconciliation' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <span>Reconciliation Queue</span>
            {feedItems.filter(f => f.status === 'suggested_match' || f.status === 'unmatched').length > 0 && (
              <span className="bg-amber-100 text-amber-800 text-[10px] px-1.5 py-0.2 rounded-full font-bold">
                {feedItems.filter(f => f.status === 'suggested_match' || f.status === 'unmatched').length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('reminders')}
            className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors flex items-center space-x-1.5 ${
              activeTab === 'reminders' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <span>Reminders & Automation</span>
          </button>

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
            Taxes & Discounts
          </button>

          {isAdmin && (
            <>
              <button
                onClick={() => setActiveTab('staff')}
                className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
                  activeTab === 'staff' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Staff RBAC ({staffList.length})
              </button>
              <button
                onClick={() => setActiveTab('customers')}
                className={`pb-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
                  activeTab === 'customers' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Customer Accounts ({customerBusinesses.length})
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

      {/* Tab: Subscription Requests */}
      {activeTab === 'requests' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Inbound Subscription Requests</h2>
              <p className="text-xs text-slate-500">Inquiries and seat sizing requirements initiated by customer organizations.</p>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Reference</th>
                  <th className="px-4 py-3">Request Type</th>
                  <th className="px-4 py-3">Requested Seats</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Notes</th>
                  <th className="px-4 py-3">Submitted</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {requestsList.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-slate-500">No customer requests submitted yet.</td>
                  </tr>
                ) : (
                  requestsList.map((req) => (
                    <tr key={req.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-blue-700">{req.reference}</td>
                      <td className="px-4 py-3 capitalize">{req.request_type.replace('_', ' ')}</td>
                      <td className="px-4 py-3 font-medium">{req.requested_quantity} seats</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-medium border capitalize ${
                          req.status === 'new' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                          req.status === 'clarification_required' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                          req.status === 'quoted' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                          req.status === 'approved_accepted' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          'bg-slate-100 text-slate-700 border-slate-200'
                        }`}>
                          {req.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-500 truncate max-w-xs">{req.notes || 'None'}</td>
                      <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                        {new Date(req.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 space-x-2">
                        <button
                          onClick={() => setSelectedRequest(req)}
                          className="px-2 py-1 border border-slate-200 rounded text-slate-700 hover:bg-slate-100 text-[11px] font-medium"
                        >
                          Activity ({req.activities.length})
                        </button>
                        <button
                          onClick={() => {
                            setQuoteForm({
                              business_id: req.business_id,
                              request_id: req.id,
                              payment_terms: 'net_30',
                              validity_days: 30,
                              lines: [{
                                product_id: req.product_id || (products[0]?.id || 1),
                                plan_id: req.plan_id || (plans[0]?.id || 1),
                                quantity: req.requested_quantity,
                                unit_price: plans[0] ? String(plans[0].base_price) : '1500.00',
                                discount_percent: '0.00',
                                tax_rate_percent: '18.00'
                              }]
                            });
                            setShowCreateQuoteModal(true);
                          }}
                          className="px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded hover:bg-blue-100 text-[11px] font-medium"
                        >
                          Prepare Quote
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

      {/* Tab: Quotations & Versioning */}
      {activeTab === 'quotations' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Commercial Quotations</h2>
              <p className="text-xs text-slate-500">
                Multi-version commercial proposals. Every version requires mandatory Admin approval before customer release.
              </p>
            </div>
            <button
              onClick={() => setShowCreateQuoteModal(true)}
              className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 inline-flex items-center space-x-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Quotation</span>
            </button>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Quote Number</th>
                  <th className="px-4 py-3">Version</th>
                  <th className="px-4 py-3">Total Amount (₹)</th>
                  <th className="px-4 py-3">Quotation Status</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {quotationsList.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-500">No quotations prepared yet.</td>
                  </tr>
                ) : (
                  quotationsList.map((q) => {
                    const latestVer = q.versions[0];
                    return (
                      <tr key={q.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-mono font-bold text-slate-900">{q.quotation_number}</td>
                        <td className="px-4 py-3">
                          <span className="font-mono bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                            v{q.current_version_number} ({q.versions.length} version{q.versions.length > 1 ? 's' : ''})
                          </span>
                        </td>
                        <td className="px-4 py-3 font-bold text-slate-900">
                          ₹{latestVer ? parseFloat(latestVer.final_total).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-medium border capitalize ${
                            q.status === 'approved' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                            q.status === 'submitted_for_approval' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                            q.status === 'accepted' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                            q.status === 'changes_requested' ? 'bg-orange-50 text-orange-700 border-orange-200' :
                            'bg-red-50 text-red-700 border-red-200'
                          }`}>
                            {q.status.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                          {new Date(q.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 space-x-1.5 whitespace-nowrap">
                          <button
                            onClick={() => setSelectedQuotation(q)}
                            className="px-2 py-1 border border-slate-200 rounded text-slate-700 hover:bg-slate-100 text-[11px] font-medium"
                          >
                            Inspect Versions
                          </button>
                          {q.status !== 'accepted' && (
                            <button
                              onClick={() => {
                                setSelectedQuotation(q);
                                if (latestVer) {
                                  setReviseForm({
                                    revision_reason: '',
                                    payment_terms: latestVer.payment_terms,
                                    validity_days: 30,
                                    lines: latestVer.lines.map(l => ({
                                      product_id: l.product_id,
                                      plan_id: l.plan_id,
                                      quantity: l.quantity,
                                      unit_price: String(l.unit_price),
                                      discount_percent: String(l.discount_percent),
                                      tax_rate_percent: String(l.tax_rate_percent)
                                    }))
                                  });
                                }
                                setShowReviseModal(true);
                              }}
                              className="px-2 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded hover:bg-amber-100 text-[11px] font-medium"
                            >
                              + Revise (v{q.current_version_number + 1})
                            </button>
                          )}
                          {q.versions.length > 1 && (
                            <button
                              onClick={() => handleOpenDiff(q.id, 1, q.current_version_number)}
                              className="px-2 py-1 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded hover:bg-indigo-100 text-[11px] font-medium inline-flex items-center space-x-1"
                            >
                              <GitCompare className="w-3 h-3" />
                              <span>Diff</span>
                            </button>
                          )}
                          {q.status === 'accepted' && (
                            <button
                              onClick={() => setGenerateInvoiceModal({
                                quoteId: q.id,
                                quoteNumber: q.quotation_number,
                                versionNumber: latestVer ? latestVer.version_number : 1
                              })}
                              className="px-2 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded hover:bg-emerald-100 text-[11px] font-medium inline-flex items-center space-x-1"
                            >
                              <Receipt className="w-3 h-3" />
                              <span>Invoice</span>
                            </button>
                          )}
                          <button
                            onClick={() => handleDownloadQuotePdf(q.id, latestVer?.version_number, q.quotation_number)}
                            className="px-2 py-1 bg-slate-50 text-slate-700 border border-slate-200 rounded hover:bg-slate-100 text-[11px] font-medium inline-flex items-center space-x-1"
                            title="Download Quotation PDF"
                          >
                            <Download className="w-3 h-3" />
                            <span>PDF</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Admin Approval Queue */}
      {isAdmin && activeTab === 'approval_queue' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Mandatory Admin Approval Queue</h2>
            <p className="text-xs text-slate-500">
              Quotation versions submitted by sales. Every version requires executive approval before being visible to the customer.
            </p>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Quotation Number</th>
                  <th className="px-4 py-3">Version</th>
                  <th className="px-4 py-3">Line Details</th>
                  <th className="px-4 py-3">Subtotal</th>
                  <th className="px-4 py-3">Discount</th>
                  <th className="px-4 py-3">Tax</th>
                  <th className="px-4 py-3">Final Total</th>
                  <th className="px-4 py-3">Decision Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {pendingApprovalQuotes.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-slate-500">
                      Zero quotations currently awaiting Admin review. All submitted proposals have been processed.
                    </td>
                  </tr>
                ) : (
                  pendingApprovalQuotes.map((q) => {
                    const ver = q.versions[0];
                    return (
                      <tr key={q.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-mono font-bold text-slate-900">{q.quotation_number}</td>
                        <td className="px-4 py-3 font-mono">v{ver.version_number}</td>
                        <td className="px-4 py-3">
                          {ver.lines.map(l => (
                            <div key={l.id} className="text-[11px]">
                              {l.quantity} seats • {l.description}
                            </div>
                          ))}
                        </td>
                        <td className="px-4 py-3">₹{parseFloat(ver.subtotal).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        <td className="px-4 py-3 text-red-600">₹{parseFloat(ver.discount_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        <td className="px-4 py-3">₹{parseFloat(ver.tax_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        <td className="px-4 py-3 font-bold text-slate-900">₹{parseFloat(ver.final_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        <td className="px-4 py-3 space-x-1 whitespace-nowrap">
                          <button
                            onClick={() => setAdminDecisionModal({
                              quoteId: q.id,
                              versionNumber: ver.version_number,
                              decisionType: 'admin_approved',
                              reason: 'Commercial terms approved by Administrator.'
                            })}
                            className="px-2 py-1 bg-emerald-600 text-white rounded font-medium hover:bg-emerald-700 text-[11px]"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => setAdminDecisionModal({
                              quoteId: q.id,
                              versionNumber: ver.version_number,
                              decisionType: 'admin_changes_requested',
                              reason: ''
                            })}
                            className="px-2 py-1 bg-amber-600 text-white rounded font-medium hover:bg-amber-700 text-[11px]"
                          >
                            Request Changes
                          </button>
                          <button
                            onClick={() => setAdminDecisionModal({
                              quoteId: q.id,
                              versionNumber: ver.version_number,
                              decisionType: 'admin_rejected',
                              reason: ''
                            })}
                            className="px-2 py-1 bg-red-600 text-white rounded font-medium hover:bg-red-700 text-[11px]"
                          >
                            Reject
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Subscriptions */}
      {activeTab === 'subscriptions' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Commercial Subscriptions</h2>
              <p className="text-xs text-slate-500">
                Active and confirmed contracts generated upon customer acceptance of Admin-approved quotation versions.
              </p>
            </div>
            {(isAdmin || isFinance) && (
              <button
                onClick={() => setRecurringModal(true)}
                className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 inline-flex items-center space-x-1.5"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Run Recurring Billing</span>
              </button>
            )}
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Subscription Ref</th>
                  <th className="px-4 py-3">Customer Business</th>
                  <th className="px-4 py-3">Seats & Products</th>
                  <th className="px-4 py-3">Recurring Total (₹)</th>
                  <th className="px-4 py-3">Frequency</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Next Billing</th>
                  <th className="px-4 py-3">Lifecycle Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {subscriptionsList.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-slate-500">
                      No subscriptions confirmed yet. A subscription is created when a customer accepts an Admin-approved quotation.
                    </td>
                  </tr>
                ) : (
                  subscriptionsList.map((sub) => (
                    <tr key={sub.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-slate-900">{sub.subscription_number}</td>
                      <td className="px-4 py-3 font-medium">Business #{sub.business_id}</td>
                      <td className="px-4 py-3">
                        {sub.lines.map(l => (
                          <div key={l.id} className="text-[11px]">
                            {l.quantity} seats • Product #{l.product_id}
                          </div>
                        ))}
                      </td>
                      <td className="px-4 py-3 font-bold text-slate-900">
                        ₹{parseFloat(sub.total_recurring_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 capitalize">{sub.billing_frequency}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-medium border capitalize ${
                          sub.status === 'active' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          sub.status === 'confirmed' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                          sub.status === 'paused' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                          'bg-slate-100 text-slate-700 border-slate-200'
                        }`}>
                          {sub.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-slate-500">
                        {sub.next_billing_date ? new Date(sub.next_billing_date).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="px-4 py-3 space-x-1">
                        <button
                          onClick={() => handleToggleSubStatus(sub.id, sub.status)}
                          className="px-2 py-1 border border-slate-200 rounded text-slate-700 hover:bg-slate-100 text-[11px] font-medium"
                        >
                          {sub.status === 'active' ? 'Pause' : 'Activate'}
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

      {/* Tab: Invoices */}
      {activeTab === 'invoices' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Invoices & Receivables</h2>
              <p className="text-xs text-slate-500">
                Commercial tax invoices generated from accepted quotation versions and recurring subscription billing cycles.
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {(isAdmin || isFinance) && (
                <>
                  <button
                    onClick={() => setRecurringModal(true)}
                    className="px-3 py-1.5 border border-slate-300 bg-white text-slate-700 rounded-md text-xs font-medium hover:bg-slate-50 inline-flex items-center space-x-1.5"
                  >
                    <Play className="w-3.5 h-3.5 text-blue-600" />
                    <span>Run Recurring Billing</span>
                  </button>
                  <button
                    onClick={() => setShowRecordPaymentModal(true)}
                    className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 inline-flex items-center space-x-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Record Payment</span>
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Total Invoiced</span>
              <div className="text-lg font-bold text-slate-900 mt-1">
                ₹{invoicesList.reduce((acc, i) => acc + parseFloat(i.final_total || '0'), 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <span className="text-[10px] text-slate-400">{invoicesList.length} total invoice(s)</span>
            </div>

            <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Collected</span>
              <div className="text-lg font-bold text-emerald-700 mt-1">
                ₹{invoicesList.reduce((acc, i) => acc + parseFloat(i.amount_paid || '0'), 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <span className="text-[10px] text-emerald-600 font-medium">Recorded receipts</span>
            </div>

            <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Outstanding Balance</span>
              <div className="text-lg font-bold text-amber-700 mt-1">
                ₹{invoicesList.reduce((acc, i) => acc + parseFloat(i.remaining_balance || '0'), 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <span className="text-[10px] text-amber-600 font-medium">Pending collection</span>
            </div>

            <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Fully Paid</span>
              <div className="text-lg font-bold text-blue-700 mt-1">
                {invoicesList.filter(i => i.status === 'paid').length}
              </div>
              <span className="text-[10px] text-slate-400">Of {invoicesList.length} invoices</span>
            </div>
          </div>

          {/* Invoices Table */}
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Invoice Number</th>
                  <th className="px-4 py-3">Customer Business</th>
                  <th className="px-4 py-3">Billing Cycle</th>
                  <th className="px-4 py-3">Issue / Due Date</th>
                  <th className="px-4 py-3">Total (₹)</th>
                  <th className="px-4 py-3">Paid (₹)</th>
                  <th className="px-4 py-3">Balance Due (₹)</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {invoicesList.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-slate-500">
                      No invoices generated yet. Invoices are produced from accepted quotations or automated recurring billing.
                    </td>
                  </tr>
                ) : (
                  invoicesList.map((inv) => {
                    const biz = customerBusinesses.find(b => b.id === inv.business_id);
                    return (
                      <tr key={inv.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-mono font-bold text-slate-900">{inv.invoice_number}</td>
                        <td className="px-4 py-3 font-medium">{biz ? biz.company_name : `Business #${inv.business_id}`}</td>
                        <td className="px-4 py-3 font-mono text-[11px] text-slate-500">{inv.billing_period}</td>
                        <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                          {new Date(inv.issue_date).toLocaleDateString()} / {new Date(inv.due_date).toLocaleDateString()}
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
                        <td className="px-4 py-3 space-x-1.5 whitespace-nowrap">
                          <button
                            onClick={() => handleDownloadInvoicePdf(inv.id, inv.invoice_number)}
                            className="px-2 py-1 bg-slate-50 text-slate-700 border border-slate-200 rounded hover:bg-slate-100 text-[11px] font-medium inline-flex items-center space-x-1"
                            title="Download Tax Invoice PDF"
                          >
                            <Download className="w-3 h-3" />
                            <span>PDF</span>
                          </button>
                          {parseFloat(inv.remaining_balance) > 0 && (isAdmin || isFinance) && (
                            <button
                              onClick={() => {
                                setPaymentForm({
                                  business_id: inv.business_id,
                                  amount: inv.remaining_balance,
                                  payment_method: 'bank_transfer',
                                  reference_number: '',
                                  notes: `Payment for ${inv.invoice_number}`,
                                  selected_invoice_id: inv.id,
                                });
                                setShowRecordPaymentModal(true);
                              }}
                              className="px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded hover:bg-blue-100 text-[11px] font-medium inline-flex items-center space-x-1"
                            >
                              <CreditCard className="w-3 h-3" />
                              <span>Pay</span>
                            </button>
                          )}
                          {(isAdmin || isFinance) && inv.status !== 'cancelled' && (
                            <select
                              value={inv.status}
                              onChange={(e) => handleUpdateInvoiceStatus(inv.id, e.target.value)}
                              className="px-1.5 py-1 border border-slate-200 rounded text-[11px] text-slate-600 bg-white"
                            >
                              <option value="confirmed">Confirmed</option>
                              <option value="partially_paid">Partially Paid</option>
                              <option value="paid">Paid</option>
                              <option value="overdue">Overdue</option>
                              <option value="cancelled">Cancelled</option>
                            </select>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Payments */}
      {activeTab === 'payments' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Payments & Reconciliation</h2>
              <p className="text-xs text-slate-500">
                Collections recorded via bank transfer, UPI, card, or cash, with automatic or manual allocation to customer invoices.
              </p>
            </div>
            {(isAdmin || isFinance) && (
              <button
                onClick={() => {
                  setPaymentForm({
                    business_id: customerBusinesses[0]?.id || 1,
                    amount: '',
                    payment_method: 'bank_transfer',
                    reference_number: '',
                    notes: '',
                    selected_invoice_id: 0,
                  });
                  setShowRecordPaymentModal(true);
                }}
                className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 inline-flex items-center space-x-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Record Payment</span>
              </button>
            )}
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Total Collections</span>
              <div className="text-lg font-bold text-emerald-700 mt-1">
                ₹{paymentsList.reduce((acc, p) => acc + parseFloat(p.amount || '0'), 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <span className="text-[10px] text-slate-400">{paymentsList.length} transactions recorded</span>
            </div>

            <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Reconciled Payments</span>
              <div className="text-lg font-bold text-blue-700 mt-1">
                {paymentsList.filter(p => p.reconciliation_status === 'reconciled').length}
              </div>
              <span className="text-[10px] text-blue-600 font-medium">100% matched to invoices</span>
            </div>

            <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Unallocated / Partial</span>
              <div className="text-lg font-bold text-amber-700 mt-1">
                {paymentsList.filter(p => p.reconciliation_status !== 'reconciled').length}
              </div>
              <span className="text-[10px] text-amber-600 font-medium">Requiring manual match</span>
            </div>
          </div>

          {/* Payments Table */}
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Payment Number</th>
                  <th className="px-4 py-3">Customer Business</th>
                  <th className="px-4 py-3">Amount (₹)</th>
                  <th className="px-4 py-3">Payment Method</th>
                  <th className="px-4 py-3">Payment Date</th>
                  <th className="px-4 py-3">UTR / Reference</th>
                  <th className="px-4 py-3">Reconciliation Status</th>
                  <th className="px-4 py-3">Allocations</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {paymentsList.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-slate-500">
                      No payments recorded yet. Click "Record Payment" to post collections against invoices.
                    </td>
                  </tr>
                ) : (
                  paymentsList.map((pay) => {
                    const biz = customerBusinesses.find(b => b.id === pay.business_id);
                    return (
                      <tr key={pay.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-mono font-bold text-slate-900">{pay.payment_number}</td>
                        <td className="px-4 py-3 font-medium">{biz ? biz.company_name : `Business #${pay.business_id}`}</td>
                        <td className="px-4 py-3 font-bold text-emerald-700">
                          ₹{parseFloat(pay.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-3 capitalize">{pay.payment_method.replace('_', ' ')}</td>
                        <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                          {new Date(pay.payment_date).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 font-mono text-[11px] text-slate-600">
                          {pay.reference_number || 'N/A'}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-medium border capitalize ${
                            pay.reconciliation_status === 'reconciled' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                            pay.reconciliation_status === 'partially_allocated' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                            'bg-slate-100 text-slate-700 border-slate-200'
                          }`}>
                            {pay.reconciliation_status.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {pay.allocations && pay.allocations.length > 0 ? (
                            pay.allocations.map(a => (
                              <span key={a.id} className="bg-slate-100 text-slate-800 px-1.5 py-0.5 rounded text-[10px] mr-1 border border-slate-200">
                                Inv #{a.invoice_id}: ₹{parseFloat(a.allocated_amount).toLocaleString('en-IN')}
                              </span>
                            ))
                          ) : (
                            <span className="text-slate-400 text-[11px]">Unallocated</span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Finance Reconciliation Queue */}
      {activeTab === 'reconciliation' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Finance Reconciliation Queue</h2>
              <p className="text-xs text-slate-500">Automated bank statement parsing, confidence-scored matching against open invoices, and dispute resolution.</p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setShowIngestModal(true)}
                className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700 flex items-center space-x-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Ingest Bank Feed Item</span>
              </button>
            </div>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
              <span className="text-xs text-slate-500 block">Total Feed Items</span>
              <span className="text-xl font-bold text-slate-900">{feedItems.length}</span>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
              <span className="text-xs text-slate-500 block">Suggested Matches</span>
              <span className="text-xl font-bold text-amber-600">
                {feedItems.filter(f => f.status === 'suggested_match').length}
              </span>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
              <span className="text-xs text-slate-500 block">Reconciled</span>
              <span className="text-xl font-bold text-emerald-600">
                {feedItems.filter(f => f.status === 'reconciled').length}
              </span>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
              <span className="text-xs text-slate-500 block">Disputed / Unmatched</span>
              <span className="text-xl font-bold text-red-600">
                {feedItems.filter(f => f.status === 'disputed' || f.status === 'unmatched').length}
              </span>
            </div>
          </div>

          {/* Filters */}
          <div className="flex space-x-2 items-center text-xs">
            <span className="text-slate-500 font-medium">Filter Status:</span>
            {['all', 'suggested_match', 'unmatched', 'reconciled', 'disputed'].map(st => (
              <button
                key={st}
                onClick={() => setFeedFilterStatus(st)}
                className={`px-2.5 py-1 rounded text-xs font-medium border capitalize ${
                  feedFilterStatus === st
                    ? 'bg-blue-50 text-blue-700 border-blue-300'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                {st.replace(/_/g, ' ')}
              </button>
            ))}
          </div>

          {/* Feed Items Table */}
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
                  <th className="px-4 py-2.5">TX ID / Account</th>
                  <th className="px-4 py-2.5">Date</th>
                  <th className="px-4 py-2.5">Narration & Sender</th>
                  <th className="px-4 py-2.5">Amount</th>
                  <th className="px-4 py-2.5">Candidate Match</th>
                  <th className="px-4 py-2.5">Confidence</th>
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {feedItems.filter(f => feedFilterStatus === 'all' || f.status === feedFilterStatus).length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-slate-500">
                      No bank feed items match the selected filter.
                    </td>
                  </tr>
                ) : (
                  feedItems
                    .filter(f => feedFilterStatus === 'all' || f.status === feedFilterStatus)
                    .map((item) => {
                      const suggInv = invoicesList.find(i => i.id === item.suggested_invoice_id);
                      const suggBiz = customerBusinesses.find(b => b.id === item.suggested_business_id);
                      const confPercent = Math.round(parseFloat(item.confidence_score || '0') * 100);

                      return (
                        <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                          <td className="px-4 py-3">
                            <span className="font-mono font-bold text-slate-900 block">{item.transaction_id}</span>
                            <span className="text-[10px] text-slate-400 font-mono">{item.bank_account_number || 'Direct Feed'}</span>
                          </td>
                          <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                            {new Date(item.transaction_date).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3 max-w-xs">
                            <p className="font-mono text-[11px] text-slate-900 truncate" title={item.raw_narration}>
                              {item.raw_narration}
                            </p>
                            {item.sender_name && (
                              <span className="text-[10px] text-slate-500 block">Sender: {item.sender_name}</span>
                            )}
                            {item.parsed_reference && (
                              <span className="text-[10px] text-blue-600 font-mono block">Parsed Ref: {item.parsed_reference}</span>
                            )}
                          </td>
                          <td className="px-4 py-3 font-bold text-slate-900">
                            ₹{parseFloat(item.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="px-4 py-3">
                            {suggInv ? (
                              <div>
                                <span className="font-mono font-bold text-blue-600 block">{suggInv.invoice_number}</span>
                                <span className="text-[10px] text-slate-500">{suggBiz?.company_name || 'Customer'} (Bal: ₹{parseFloat(suggInv.remaining_balance).toLocaleString('en-IN')})</span>
                              </div>
                            ) : (
                              <span className="text-slate-400 italic">No direct match</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {confPercent > 0 ? (
                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold ${
                                confPercent >= 90 ? 'bg-emerald-100 text-emerald-800' :
                                confPercent >= 70 ? 'bg-amber-100 text-amber-800' :
                                'bg-slate-100 text-slate-700'
                              }`}>
                                {confPercent}%
                              </span>
                            ) : (
                              <span className="text-slate-400">0%</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded text-[11px] font-medium border capitalize ${
                              item.status === 'reconciled' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                              item.status === 'suggested_match' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                              item.status === 'disputed' ? 'bg-red-50 text-red-700 border-red-200' :
                              'bg-slate-100 text-slate-700 border-slate-200'
                            }`}>
                              {item.status.replace(/_/g, ' ')}
                            </span>
                            {item.reconciliation_notes && (
                              <p className="text-[10px] text-slate-500 mt-1 italic truncate max-w-xs" title={item.reconciliation_notes}>
                                {item.reconciliation_notes}
                              </p>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {item.status !== 'reconciled' && item.status !== 'disputed' && (
                              <div className="flex justify-end space-x-1.5">
                                <button
                                  onClick={() => setConfirmMatchModal({
                                    item,
                                    invoice_id: item.suggested_invoice_id || (invoicesList.find(i => i.status !== 'paid')?.id || 0),
                                    amount: item.amount,
                                    notes: `Verified against narration ${item.raw_narration}`
                                  })}
                                  className="px-2 py-1 bg-emerald-600 text-white rounded hover:bg-emerald-700 font-medium text-[11px]"
                                >
                                  Confirm Match
                                </button>
                                <button
                                  onClick={() => setDisputeModal({ item, reason: '' })}
                                  className="px-2 py-1 border border-red-300 text-red-600 rounded hover:bg-red-50 font-medium text-[11px]"
                                >
                                  Dispute
                                </button>
                              </div>
                            )}
                            {item.status === 'reconciled' && (
                              <span className="text-[11px] text-emerald-600 font-medium inline-flex items-center space-x-1">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>Reconciled</span>
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Reminders & Automation */}
      {activeTab === 'reminders' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Automated Reminders & Governance</h2>
              <p className="text-xs text-slate-500">Scheduled dunning workflows: 3 days prior, on due date, 7 days overdue, and 14 days overdue final notice.</p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  setSweepResult(null);
                  setShowSweepModal(true);
                }}
                className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700 flex items-center space-x-1.5"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Run Reminder Sweep</span>
              </button>
              {isAdmin && (
                <button
                  onClick={() => setShowRuleModal(true)}
                  className="px-3 py-1.5 border border-slate-300 bg-white text-slate-700 rounded text-xs font-medium hover:bg-slate-50 flex items-center space-x-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>New Reminder Rule</span>
                </button>
              )}
            </div>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
              <span className="text-xs text-slate-500 block">Configured Rules</span>
              <span className="text-xl font-bold text-slate-900">{reminderRules.length}</span>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
              <span className="text-xs text-slate-500 block">Reminders Dispatched (Lifetime)</span>
              <span className="text-xl font-bold text-blue-600">{reminderHistory.length}</span>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
              <span className="text-xs text-slate-500 block">Overdue Invoices Monitored</span>
              <span className="text-xl font-bold text-amber-600">
                {invoicesList.filter(i => i.status === 'overdue' || (i.status === 'confirmed' && new Date(i.due_date) < new Date())).length}
              </span>
            </div>
          </div>

          {/* Governance Rules Table */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wider">Configured Dunning & Notice Rules</h3>
            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
                    <th className="px-4 py-2.5">Rule Name</th>
                    <th className="px-4 py-2.5">Trigger Condition</th>
                    <th className="px-4 py-2.5">Offset</th>
                    <th className="px-4 py-2.5">Channel</th>
                    <th className="px-4 py-2.5">Escalation</th>
                    <th className="px-4 py-2.5">Subject Template</th>
                    <th className="px-4 py-2.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-800">
                  {reminderRules.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-6 text-center text-slate-500">
                        No reminder rules found.
                      </td>
                    </tr>
                  ) : (
                    reminderRules.map((rule) => (
                      <tr key={rule.id} className="hover:bg-slate-50">
                        <td className="px-4 py-3 font-semibold text-slate-900">{rule.name}</td>
                        <td className="px-4 py-3 capitalize">{rule.trigger_type.replace(/_/g, ' ')}</td>
                        <td className="px-4 py-3 font-mono font-bold">
                          {rule.days_offset < 0 ? `${Math.abs(rule.days_offset)} days before` :
                           rule.days_offset === 0 ? 'On Due Date' :
                           `${rule.days_offset} days after`}
                        </td>
                        <td className="px-4 py-3">
                          <span className="uppercase text-[10px] font-bold px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
                            {rule.channel}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold capitalize border ${
                            rule.escalation_level === 'final_notice' ? 'bg-red-50 text-red-700 border-red-200' :
                            rule.escalation_level === 'urgent' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                            'bg-slate-100 text-slate-700 border-slate-200'
                          }`}>
                            {rule.escalation_level.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-[11px] text-slate-600 max-w-xs truncate" title={rule.subject_template}>
                          {rule.subject_template}
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center text-emerald-600 font-medium space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Active</span>
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Reminder Dispatch History */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wider">Live Notification & Delivery History</h3>
            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
                    <th className="px-4 py-2.5">Sent Timestamp</th>
                    <th className="px-4 py-2.5">Customer Organization</th>
                    <th className="px-4 py-2.5">Recipient</th>
                    <th className="px-4 py-2.5">Invoice #</th>
                    <th className="px-4 py-2.5">Channel</th>
                    <th className="px-4 py-2.5">Subject & Preview</th>
                    <th className="px-4 py-2.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-800">
                  {reminderHistory.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-6 text-center text-slate-500">
                        No reminder notifications dispatched yet. Execute a reminder sweep to evaluate open invoices.
                      </td>
                    </tr>
                  ) : (
                    reminderHistory.map((notif) => {
                      const biz = customerBusinesses.find(b => b.id === notif.business_id);
                      const inv = invoicesList.find(i => i.id === notif.invoice_id);

                      return (
                        <tr key={notif.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                            {new Date(notif.sent_at).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 font-medium text-slate-900">
                            {biz ? biz.company_name : `Business #${notif.business_id}`}
                          </td>
                          <td className="px-4 py-3 font-mono text-[11px] text-slate-600">
                            {notif.recipient_email}
                          </td>
                          <td className="px-4 py-3 font-mono font-bold text-blue-600">
                            {inv ? inv.invoice_number : (notif.invoice_id ? `Inv #${notif.invoice_id}` : 'General')}
                          </td>
                          <td className="px-4 py-3">
                            <span className="uppercase text-[10px] font-bold px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
                              {notif.channel}
                            </span>
                          </td>
                          <td className="px-4 py-3 max-w-sm">
                            <span className="font-semibold text-slate-900 block truncate" title={notif.subject}>
                              {notif.subject}
                            </span>
                            <span className="text-[11px] text-slate-500 block truncate" title={notif.content}>
                              {notif.content}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 capitalize">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>{notif.status}</span>
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Products & Variants */}
      {activeTab === 'catalog' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Products & Catalog</h2>
              <p className="text-xs text-slate-500">Manage SaaS offerings and variants.</p>
            </div>
            {isAdmin && (
              <button
                onClick={() => setShowProductModal(true)}
                className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 inline-flex items-center space-x-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Product</span>
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {products.map((p) => (
              <div key={p.id} className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm space-y-2">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-slate-900 text-sm">{p.name}</h3>
                    <span className="font-mono text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">{p.code}</span>
                  </div>
                  <span className="text-xs font-bold text-slate-900">₹{p.sales_price}</span>
                </div>
                <p className="text-xs text-slate-600 line-clamp-2">{p.description || 'No description.'}</p>
                <div className="pt-2 border-t border-slate-100 flex justify-between text-[11px] text-slate-500">
                  <span>Variants: {p.variants?.length || 0}</span>
                  <span className="capitalize">{p.product_type}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Plans */}
      {activeTab === 'plans' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Subscription Plans</h2>
              <p className="text-xs text-slate-500">Billing cadence and pricing tiers.</p>
            </div>
            {isAdmin && (
              <button
                onClick={() => setShowPlanModal(true)}
                className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 inline-flex items-center space-x-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create Plan</span>
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {plans.map((pl) => (
              <div key={pl.id} className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm space-y-2">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-slate-900 text-sm">{pl.name}</h3>
                    <span className="font-mono text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">{pl.code}</span>
                  </div>
                  <span className="text-xs font-bold text-blue-700">₹{pl.base_price}/{pl.billing_frequency}</span>
                </div>
                <div className="text-xs text-slate-600 space-y-1 pt-2 border-t border-slate-100">
                  <div>Min Quantity: {pl.min_quantity} seat(s)</div>
                  <div>Auto-Renew: {pl.auto_renew ? 'Yes' : 'No'}</div>
                  <div>Trial Period: {pl.trial_days} days</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Taxes & Discounts */}
      {activeTab === 'taxes_discounts' && (
        <div className="space-y-6">
          {/* Tax Rates */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Tax Rates (GST)</h3>
                <p className="text-xs text-slate-500">Applicable tax structures.</p>
              </div>
              {isAdmin && (
                <button
                  onClick={() => setShowTaxModal(true)}
                  className="px-2.5 py-1 bg-slate-800 text-white rounded text-xs hover:bg-slate-900 inline-flex items-center space-x-1"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add Tax Rate</span>
                </button>
              )}
            </div>

            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 uppercase font-semibold tracking-wider">
                  <tr>
                    <th className="px-4 py-2.5">Name</th>
                    <th className="px-4 py-2.5">Rate Percent</th>
                    <th className="px-4 py-2.5">Type</th>
                    <th className="px-4 py-2.5">Active</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-800">
                  {taxes.map((t) => (
                    <tr key={t.id}>
                      <td className="px-4 py-2.5 font-medium">{t.name}</td>
                      <td className="px-4 py-2.5 font-bold">{t.rate_percent}%</td>
                      <td className="px-4 py-2.5">{t.is_compound ? 'Compound' : 'Simple'}</td>
                      <td className="px-4 py-2.5">{t.is_active ? 'Active' : 'Inactive'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Discount Rules */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Discount Governance Rules</h3>
                <p className="text-xs text-slate-500">Volume thresholds and administrative approval ceilings.</p>
              </div>
              {isAdmin && (
                <button
                  onClick={() => setShowDiscountModal(true)}
                  className="px-2.5 py-1 bg-slate-800 text-white rounded text-xs hover:bg-slate-900 inline-flex items-center space-x-1"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add Discount Rule</span>
                </button>
              )}
            </div>

            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 uppercase font-semibold tracking-wider">
                  <tr>
                    <th className="px-4 py-2.5">Rule Name</th>
                    <th className="px-4 py-2.5">Type</th>
                    <th className="px-4 py-2.5">Value</th>
                    <th className="px-4 py-2.5">Min Seats</th>
                    <th className="px-4 py-2.5">Max Sales Discretion</th>
                    <th className="px-4 py-2.5">Admin Approval Req.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-800">
                  {discounts.map((d) => (
                    <tr key={d.id}>
                      <td className="px-4 py-2.5 font-medium">{d.name}</td>
                      <td className="px-4 py-2.5 capitalize">{d.discount_type}</td>
                      <td className="px-4 py-2.5 font-bold">{d.discount_type === 'percentage' ? `${d.value}%` : `₹${d.value}`}</td>
                      <td className="px-4 py-2.5">{d.min_seats} seats</td>
                      <td className="px-4 py-2.5">{d.max_allowed_sales_discount}%</td>
                      <td className="px-4 py-2.5">{d.requires_admin_approval ? 'Yes' : 'No'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Staff (Admin Only) */}
      {isAdmin && activeTab === 'staff' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Internal Staff Directory</h2>
              <p className="text-xs text-slate-500">Sales Representatives and Finance Representatives.</p>
            </div>
            <button
              onClick={() => setShowStaffModal(true)}
              className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 inline-flex items-center space-x-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Staff User</span>
            </button>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 uppercase font-semibold tracking-wider">
                <tr>
                  <th className="px-4 py-3">Full Name</th>
                  <th className="px-4 py-3">Email Address</th>
                  <th className="px-4 py-3">Staff Role</th>
                  <th className="px-4 py-3">Department</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {staffList.map((s) => (
                  <tr key={s.id}>
                    <td className="px-4 py-3 font-medium">{s.full_name}</td>
                    <td className="px-4 py-3 font-mono text-slate-500">{s.email}</td>
                    <td className="px-4 py-3 capitalize">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${
                        s.role === 'admin' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                        s.role === 'sales' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                        'bg-emerald-50 text-emerald-700 border-emerald-200'
                      }`}>
                        {s.role}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500">{s.staff_profile?.department || 'Executive'}</td>
                    <td className="px-4 py-3">
                      <span className="text-emerald-700 font-medium">Active</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Customers (Admin Only) */}
      {isAdmin && activeTab === 'customers' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Customer Organizations</h2>
            <p className="text-xs text-slate-500">Registered businesses and multi-user tenant rosters.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {customerBusinesses.map((b) => (
              <div key={b.id} className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-slate-900 text-sm">{b.company_name}</h3>
                    <p className="text-xs text-slate-500">Tax ID: {b.tax_id || 'N/A'}</p>
                  </div>
                  <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded text-[11px] font-medium uppercase">
                    {b.status}
                  </span>
                </div>

                <div className="text-xs text-slate-600">
                  <div>Contact: {b.contact_email}</div>
                  <div>Country: {b.billing_country}</div>
                </div>

                <div className="pt-2 border-t border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-700">Team Members ({b.members?.length || 0}):</span>
                  <div className="mt-1 space-y-1">
                    {b.members?.map((m) => (
                      <div key={m.id} className="text-[11px] text-slate-600 flex justify-between">
                        <span>{m.full_name} ({m.email})</span>
                        <span className="font-mono text-slate-400 capitalize">{m.role.replace('_', ' ')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Audit Trail (Admin Only) */}
      {isAdmin && activeTab === 'audit' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">System Audit Trail</h2>
            <p className="text-xs text-slate-500">Immutable ledger of state transitions and administrative actions.</p>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 uppercase font-semibold tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Timestamp</th>
                  <th className="px-4 py-2.5">Actor</th>
                  <th className="px-4 py-2.5">Role</th>
                  <th className="px-4 py-2.5">Action</th>
                  <th className="px-4 py-2.5">Entity</th>
                  <th className="px-4 py-2.5">State Change Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="px-4 py-2.5 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-2.5 font-medium">{log.actor_email}</td>
                    <td className="px-4 py-2.5 capitalize">{log.actor_role}</td>
                    <td className="px-4 py-2.5 font-mono text-blue-700">{log.action}</td>
                    <td className="px-4 py-2.5">{log.entity_type} #{log.entity_id}</td>
                    <td className="px-4 py-2.5 font-mono text-[11px] text-slate-500 truncate max-w-xs">
                      {log.after_state ? JSON.stringify(log.after_state) : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal: Activity / Clarifications on Request */}
      {selectedRequest && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <span className="text-xs font-mono text-blue-600 bg-blue-50 px-2 py-0.5 rounded font-bold">
                  {selectedRequest.reference}
                </span>
                <h3 className="text-sm font-semibold text-slate-900 mt-1 capitalize">
                  {selectedRequest.request_type.replace('_', ' ')}: {selectedRequest.requested_quantity} seat(s)
                </h3>
              </div>
              <button onClick={() => setSelectedRequest(null)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            {/* Conversation Log */}
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {selectedRequest.activities.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-4">No communications recorded on this request.</p>
              ) : (
                selectedRequest.activities.map((act) => (
                  <div
                    key={act.id}
                    className={`p-2.5 rounded text-xs ${
                      act.activity_type.includes('customer')
                        ? 'bg-slate-50 border border-slate-200 text-slate-800'
                        : act.activity_type === 'clarification_request'
                        ? 'bg-amber-50 border border-amber-200 text-amber-900'
                        : 'bg-blue-50 border border-blue-200 text-blue-900'
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

            {/* Post Activity Form */}
            <form onSubmit={handleAddRequestActivity} className="space-y-3 pt-2 border-t border-slate-200">
              <div className="flex space-x-4 text-xs">
                <label className="flex items-center space-x-1 cursor-pointer">
                  <input
                    type="radio"
                    name="activityType"
                    checked={activityType === 'sales_note'}
                    onChange={() => setActivityType('sales_note')}
                    className="text-blue-600"
                  />
                  <span>Internal Sales Note</span>
                </label>
                <label className="flex items-center space-x-1 cursor-pointer">
                  <input
                    type="radio"
                    name="activityType"
                    checked={activityType === 'clarification_request'}
                    onChange={() => setActivityType('clarification_request')}
                    className="text-blue-600"
                  />
                  <span className="text-amber-800 font-medium">Request Clarification from Customer</span>
                </label>
              </div>

              <textarea
                rows={2}
                value={requestActivityMsg}
                onChange={(e) => setRequestActivityMsg(e.target.value)}
                placeholder={activityType === 'clarification_request' ? "Ask the customer to clarify their deployment scope or seat count..." : "Add private note for the sales team..."}
                required
                className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
              />

              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setSelectedRequest(null)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-xs text-slate-700 hover:bg-slate-50"
                >
                  Close
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
                >
                  Post Activity
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Create Quotation */}
      {showCreateQuoteModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-xl w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-semibold text-slate-900">Prepare Commercial Quotation</h3>
                <p className="text-xs text-slate-500">
                  Bulk seat entry with transparent discount governance. Mandatory Admin approval is enforced.
                </p>
              </div>
              <button onClick={() => setShowCreateQuoteModal(false)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            <form onSubmit={handleCreateQuotation} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Customer Business</label>
                  <select
                    value={quoteForm.business_id}
                    onChange={(e) => setQuoteForm({ ...quoteForm, business_id: Number(e.target.value) })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded text-xs"
                  >
                    {customerBusinesses.map(b => (
                      <option key={b.id} value={b.id}>{b.company_name} (ID: {b.id})</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Payment Terms</label>
                  <select
                    value={quoteForm.payment_terms}
                    onChange={(e) => setQuoteForm({ ...quoteForm, payment_terms: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded text-xs"
                  >
                    <option value="due_on_receipt">Due on Receipt</option>
                    <option value="net_15">Net 15 Days</option>
                    <option value="net_30">Net 30 Days</option>
                    <option value="net_60">Net 60 Days</option>
                  </select>
                </div>
              </div>

              {/* Line items with bulk quantity input */}
              <div className="border border-slate-200 rounded p-3 space-y-2 bg-slate-50">
                <span className="font-semibold text-slate-800">Proposal Line Items (Bulk Seats):</span>
                {quoteForm.lines.map((line, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2 items-center">
                    <div className="col-span-4">
                      <label className="block text-[10px] text-slate-500">Product</label>
                      <select
                        value={line.product_id}
                        onChange={(e) => {
                          const updated = [...quoteForm.lines];
                          updated[idx].product_id = Number(e.target.value);
                          setQuoteForm({ ...quoteForm, lines: updated });
                        }}
                        className="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white"
                      >
                        {products.map(p => (
                          <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                      </select>
                    </div>

                    <div className="col-span-3">
                      <label className="block text-[10px] text-slate-500">Plan</label>
                      <select
                        value={line.plan_id}
                        onChange={(e) => {
                          const updated = [...quoteForm.lines];
                          const pl = plans.find(p => p.id === Number(e.target.value));
                          updated[idx].plan_id = Number(e.target.value);
                          if (pl) updated[idx].unit_price = String(pl.base_price);
                          setQuoteForm({ ...quoteForm, lines: updated });
                        }}
                        className="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white"
                      >
                        {plans.map(pl => (
                          <option key={pl.id} value={pl.id}>{pl.name} (₹{pl.base_price})</option>
                        ))}
                      </select>
                    </div>

                    <div className="col-span-2">
                      <label className="block text-[10px] text-slate-500 font-semibold text-blue-700">Quantity (Seats)</label>
                      <input
                        type="number"
                        min="1"
                        required
                        value={line.quantity}
                        onChange={(e) => {
                          const updated = [...quoteForm.lines];
                          updated[idx].quantity = Number(e.target.value);
                          setQuoteForm({ ...quoteForm, lines: updated });
                        }}
                        className="w-full px-2 py-1 border border-blue-400 rounded text-xs bg-white font-bold"
                      />
                    </div>

                    <div className="col-span-3">
                      <label className="block text-[10px] text-slate-500">Discount %</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        value={line.discount_percent}
                        onChange={(e) => {
                          const updated = [...quoteForm.lines];
                          updated[idx].discount_percent = e.target.value;
                          setQuoteForm({ ...quoteForm, lines: updated });
                        }}
                        className="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowCreateQuoteModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
                >
                  Submit for Admin Approval
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Revise Quotation Version */}
      {showReviseModal && selectedQuotation && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-xl w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-semibold text-slate-900">
                  Revise Quotation {selectedQuotation.quotation_number} (Creates v{selectedQuotation.current_version_number + 1})
                </h3>
                <p className="text-xs text-slate-500">
                  Submit a revised version. Previous versions will remain accessible for historical audit.
                </p>
              </div>
              <button onClick={() => setShowReviseModal(false)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            <form onSubmit={handleReviseQuotation} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Reason for Revision *</label>
                <textarea
                  rows={2}
                  required
                  value={reviseForm.revision_reason}
                  onChange={(e) => setReviseForm({ ...reviseForm, revision_reason: e.target.value })}
                  placeholder="e.g. Adjusted seat count from 20 to 25 and applied additional 5% strategic discount."
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div className="border border-slate-200 rounded p-3 space-y-2 bg-slate-50">
                <span className="font-semibold text-slate-800">Update Seats & Pricing:</span>
                {reviseForm.lines.map((line, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2 items-center">
                    <div className="col-span-4">
                      <label className="block text-[10px] text-slate-500">Product</label>
                      <select
                        value={line.product_id}
                        onChange={(e) => {
                          const updated = [...reviseForm.lines];
                          updated[idx].product_id = Number(e.target.value);
                          setReviseForm({ ...reviseForm, lines: updated });
                        }}
                        className="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white"
                      >
                        {products.map(p => (
                          <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                      </select>
                    </div>

                    <div className="col-span-3">
                      <label className="block text-[10px] text-slate-500">Plan</label>
                      <select
                        value={line.plan_id}
                        onChange={(e) => {
                          const updated = [...reviseForm.lines];
                          const pl = plans.find(p => p.id === Number(e.target.value));
                          updated[idx].plan_id = Number(e.target.value);
                          if (pl) updated[idx].unit_price = String(pl.base_price);
                          setReviseForm({ ...reviseForm, lines: updated });
                        }}
                        className="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white"
                      >
                        {plans.map(pl => (
                          <option key={pl.id} value={pl.id}>{pl.name} (₹{pl.base_price})</option>
                        ))}
                      </select>
                    </div>

                    <div className="col-span-2">
                      <label className="block text-[10px] text-slate-500 font-semibold text-blue-700">Quantity (Seats)</label>
                      <input
                        type="number"
                        min="1"
                        required
                        value={line.quantity}
                        onChange={(e) => {
                          const updated = [...reviseForm.lines];
                          updated[idx].quantity = Number(e.target.value);
                          setReviseForm({ ...reviseForm, lines: updated });
                        }}
                        className="w-full px-2 py-1 border border-blue-400 rounded text-xs bg-white font-bold"
                      />
                    </div>

                    <div className="col-span-3">
                      <label className="block text-[10px] text-slate-500">Discount %</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        value={line.discount_percent}
                        onChange={(e) => {
                          const updated = [...reviseForm.lines];
                          updated[idx].discount_percent = e.target.value;
                          setReviseForm({ ...reviseForm, lines: updated });
                        }}
                        className="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowReviseModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
                >
                  Submit Revision for Approval
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Inspect Versions */}
      {selectedQuotation && !showReviseModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-3xl w-full p-6 shadow-xl border border-slate-200 space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-semibold text-slate-900">
                  Version History: {selectedQuotation.quotation_number}
                </h3>
                <p className="text-xs text-slate-500">
                  Inspect all immutable snapshots created for this proposal.
                </p>
              </div>
              <button onClick={() => setSelectedQuotation(null)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            <div className="space-y-4">
              {selectedQuotation.versions.map((ver) => (
                <div key={ver.id} className="border border-slate-200 rounded-lg p-4 space-y-3 bg-slate-50">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-xs bg-white px-2 py-0.5 rounded border border-slate-200">
                        Version {ver.version_number}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[11px] font-medium border capitalize ${
                        ver.status === 'approved' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                        ver.status === 'submitted_for_approval' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                        ver.status === 'accepted' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                        'bg-slate-100 text-slate-700 border-slate-200'
                      }`}>
                        {ver.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <div className="space-x-2">
                      <button
                        onClick={() => handleDownloadQuotePdf(selectedQuotation.id, ver.version_number, selectedQuotation.quotation_number)}
                        className="px-2 py-1 bg-white border border-slate-200 rounded text-[11px] text-slate-700 hover:bg-slate-100 inline-flex items-center space-x-1"
                      >
                        <Download className="w-3 h-3" />
                        <span>PDF</span>
                      </button>
                      <span className="text-xs font-bold text-slate-900">
                        ₹{parseFloat(ver.final_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>

                  {ver.revision_reason && (
                    <p className="text-xs text-slate-600 italic">
                      Revision Note: "{ver.revision_reason}"
                    </p>
                  )}

                  {/* Line Details */}
                  <table className="min-w-full text-xs bg-white rounded border border-slate-200 divide-y divide-slate-100">
                    <thead className="bg-slate-100/60 text-slate-500 font-semibold text-[11px]">
                      <tr>
                        <th className="px-3 py-1.5 text-left">Seats</th>
                        <th className="px-3 py-1.5 text-left">Plan / Description</th>
                        <th className="px-3 py-1.5 text-right">Unit Price</th>
                        <th className="px-3 py-1.5 text-right">Discount</th>
                        <th className="px-3 py-1.5 text-right">Tax (18%)</th>
                        <th className="px-3 py-1.5 text-right">Line Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {ver.lines.map((l) => (
                        <tr key={l.id}>
                          <td className="px-3 py-1.5 font-bold">{l.quantity} seats</td>
                          <td className="px-3 py-1.5">{l.description}</td>
                          <td className="px-3 py-1.5 text-right">₹{parseFloat(l.unit_price).toLocaleString('en-IN')}</td>
                          <td className="px-3 py-1.5 text-right text-red-600">-₹{parseFloat(l.discount_amount).toLocaleString('en-IN')}</td>
                          <td className="px-3 py-1.5 text-right">₹{parseFloat(l.tax_amount).toLocaleString('en-IN')}</td>
                          <td className="px-3 py-1.5 text-right font-bold text-slate-900">₹{parseFloat(l.line_total).toLocaleString('en-IN')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-200">
              <button
                type="button"
                onClick={() => setSelectedQuotation(null)}
                className="px-4 py-1.5 bg-slate-800 text-white rounded text-xs hover:bg-slate-900"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Version Diff */}
      {diffModal && diffModal.diff && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-xl w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-semibold text-slate-900">
                  Version Diff: v{diffModal.base} vs v{diffModal.target}
                </h3>
                <p className="text-xs text-slate-500 font-mono">
                  {diffModal.diff.quotation_number}
                </p>
              </div>
              <button onClick={() => setDiffModal(null)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 border border-slate-200 rounded">
                <div>
                  <span className="text-slate-500 block text-[11px]">Subtotal Difference:</span>
                  <span className={`font-bold font-mono ${parseFloat(diffModal.diff.subtotal_diff) >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                    ₹{diffModal.diff.subtotal_diff}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[11px]">Final Total Difference:</span>
                  <span className={`font-bold font-mono ${parseFloat(diffModal.diff.final_total_diff) >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                    ₹{diffModal.diff.final_total_diff}
                  </span>
                </div>
              </div>

              <div>
                <span className="font-semibold text-slate-800 block mb-2">Line by Line Seat Count Changes:</span>
                <div className="border border-slate-200 rounded divide-y divide-slate-100">
                  {diffModal.diff.lines_comparison.map((lc, i) => (
                    <div key={i} className="p-2.5 flex justify-between items-center text-xs">
                      <div>
                        <span className="font-medium text-slate-900">{lc.description}</span>
                        <div className="text-[11px] text-slate-500">
                          v{diffModal.base}: {lc.base_quantity} seats → v{diffModal.target}: {lc.target_quantity} seats
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`font-bold font-mono ${lc.quantity_diff >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                          {lc.quantity_diff > 0 ? `+${lc.quantity_diff}` : lc.quantity_diff} seats
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-200">
              <button
                type="button"
                onClick={() => setDiffModal(null)}
                className="px-4 py-1.5 bg-slate-800 text-white rounded text-xs hover:bg-slate-900"
              >
                Close Diff
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Admin Decision */}
      {adminDecisionModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-sm font-semibold text-slate-900 capitalize">
              Confirm {adminDecisionModal.decisionType.replace('admin_', '').replace('_', ' ')}
            </h3>
            <p className="text-xs text-slate-500">
              Recording mandatory decision on Quotation #{adminDecisionModal.quoteId} v{adminDecisionModal.versionNumber}.
            </p>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">
                  Explanation / Justification Reason {adminDecisionModal.decisionType !== 'admin_approved' && '*'}
                </label>
                <textarea
                  rows={3}
                  required={adminDecisionModal.decisionType !== 'admin_approved'}
                  value={adminDecisionModal.reason}
                  onChange={(e) => setAdminDecisionModal({ ...adminDecisionModal, reason: e.target.value })}
                  placeholder="State the administrative reason for this decision..."
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setAdminDecisionModal(null)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleAdminDecision}
                  className={`px-3 py-1.5 text-white rounded font-medium ${
                    adminDecisionModal.decisionType === 'admin_approved' ? 'bg-emerald-600 hover:bg-emerald-700' :
                    adminDecisionModal.decisionType === 'admin_changes_requested' ? 'bg-amber-600 hover:bg-amber-700' :
                    'bg-red-600 hover:bg-red-700'
                  }`}
                >
                  Confirm Decision
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Generate Invoice from Quotation */}
      {generateInvoiceModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-sm font-semibold text-slate-900">
              Generate Invoice for Quotation {generateInvoiceModal.quoteNumber}
            </h3>
            <p className="text-xs text-slate-500">
              This converts accepted quotation version {generateInvoiceModal.versionNumber} into a binding tax invoice with payment terms and balance tracking.
            </p>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Custom Due Date (Optional, defaults to Payment Terms)</label>
                <input
                  type="date"
                  value={invoiceDueDate}
                  onChange={(e) => setInvoiceDueDate(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded text-xs bg-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setGenerateInvoiceModal(null)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleGenerateInvoice}
                  className="px-3 py-1.5 bg-emerald-600 text-white rounded font-medium hover:bg-emerald-700"
                >
                  Generate Tax Invoice
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Run Recurring Billing */}
      {recurringModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-sm font-semibold text-slate-900">
              Run Automated Recurring Billing
            </h3>
            <p className="text-xs text-slate-500">
              Evaluates all active subscriptions due on or before the target date. The engine guarantees strict idempotency: subscriptions already invoiced for their current period are skipped safely.
            </p>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Target Billing Date (Optional, defaults to Today)</label>
                <input
                  type="date"
                  value={recurringTargetDate}
                  onChange={(e) => setRecurringTargetDate(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded text-xs bg-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setRecurringModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleRunRecurring}
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 inline-flex items-center space-x-1"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Execute Billing Run</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Record Manual Payment */}
      {showRecordPaymentModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Record Customer Payment</h3>
                <p className="text-xs text-slate-500">Post realized collections and allocate against outstanding invoices.</p>
              </div>
              <button onClick={() => setShowRecordPaymentModal(false)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            <form onSubmit={handleRecordPayment} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Customer Business *</label>
                  <select
                    value={paymentForm.business_id}
                    onChange={(e) => {
                      const bId = Number(e.target.value);
                      setPaymentForm({ ...paymentForm, business_id: bId, selected_invoice_id: 0 });
                    }}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded text-xs bg-white"
                  >
                    {customerBusinesses.map(b => (
                      <option key={b.id} value={b.id}>{b.company_name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Payment Method *</label>
                  <select
                    value={paymentForm.payment_method}
                    onChange={(e) => setPaymentForm({ ...paymentForm, payment_method: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded text-xs bg-white"
                  >
                    <option value="bank_transfer">Bank Transfer (NEFT/RTGS/IMPS)</option>
                    <option value="upi">UPI</option>
                    <option value="card">Credit / Debit Card</option>
                    <option value="cash">Cash</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Payment Amount (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    value={paymentForm.amount}
                    onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                    placeholder="e.g. 50000.00"
                    className="w-full px-3 py-1.5 border border-slate-300 rounded text-xs font-bold bg-white"
                  />
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">UTR / Bank Reference</label>
                  <input
                    type="text"
                    value={paymentForm.reference_number}
                    onChange={(e) => setPaymentForm({ ...paymentForm, reference_number: e.target.value })}
                    placeholder="e.g. UTR-HDFC-991204"
                    className="w-full px-3 py-1.5 border border-slate-300 rounded text-xs bg-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Allocate to Invoice (Optional)</label>
                <select
                  value={paymentForm.selected_invoice_id}
                  onChange={(e) => setPaymentForm({ ...paymentForm, selected_invoice_id: Number(e.target.value) })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded text-xs bg-white"
                >
                  <option value={0}>-- Allocate Later / General Receipt --</option>
                  {invoicesList
                    .filter(i => i.business_id === paymentForm.business_id && parseFloat(i.remaining_balance) > 0)
                    .map(i => (
                      <option key={i.id} value={i.id}>
                        {i.invoice_number} (Total: ₹{parseFloat(i.final_total).toLocaleString('en-IN')}, Balance Due: ₹{parseFloat(i.remaining_balance).toLocaleString('en-IN')})
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Internal Notes</label>
                <textarea
                  rows={2}
                  value={paymentForm.notes}
                  onChange={(e) => setPaymentForm({ ...paymentForm, notes: e.target.value })}
                  placeholder="e.g. First milestone wire received via HDFC Bank."
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs bg-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowRecordPaymentModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
                >
                  Confirm & Post Payment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Catalog Modals (Admin Only) */}
      {showProductModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <h3 className="text-sm font-semibold text-slate-900">Add New Product</h3>
            <form onSubmit={handleCreateProduct} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Product Name</label>
                <input
                  type="text"
                  required
                  value={productForm.name}
                  onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Product Code</label>
                  <input
                    type="text"
                    required
                    value={productForm.code}
                    onChange={(e) => setProductForm({ ...productForm, code: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Sales Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={productForm.sales_price}
                    onChange={(e) => setProductForm({ ...productForm, sales_price: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-700 font-medium mb-1">Description</label>
                <textarea
                  rows={2}
                  value={productForm.description}
                  onChange={(e) => setProductForm({ ...productForm, description: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setShowProductModal(false)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Cancel</button>
                <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700">Save Product</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showPlanModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <h3 className="text-sm font-semibold text-slate-900">Create Subscription Plan</h3>
            <form onSubmit={handleCreatePlan} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Product</label>
                <select
                  value={planForm.product_id}
                  onChange={(e) => setPlanForm({ ...planForm, product_id: Number(e.target.value) })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                >
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Plan Name</label>
                  <input
                    type="text"
                    required
                    value={planForm.name}
                    onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Plan Code</label>
                  <input
                    type="text"
                    required
                    value={planForm.code}
                    onChange={(e) => setPlanForm({ ...planForm, code: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Frequency</label>
                  <select
                    value={planForm.billing_frequency}
                    onChange={(e) => setPlanForm({ ...planForm, billing_frequency: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
                  >
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Base Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={planForm.base_price}
                    onChange={(e) => setPlanForm({ ...planForm, base_price: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setShowPlanModal(false)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Cancel</button>
                <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700">Save Plan</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showTaxModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-sm w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <h3 className="text-sm font-semibold text-slate-900">Add Tax Rate</h3>
            <form onSubmit={handleCreateTax} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Tax Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. GST 18%"
                  value={taxForm.name}
                  onChange={(e) => setTaxForm({ ...taxForm, name: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-medium mb-1">Rate Percent (%)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="18.00"
                  value={taxForm.rate_percent}
                  onChange={(e) => setTaxForm({ ...taxForm, rate_percent: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setShowTaxModal(false)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Cancel</button>
                <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700">Save Tax</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showDiscountModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <h3 className="text-sm font-semibold text-slate-900">Add Discount Governance Rule</h3>
            <form onSubmit={handleCreateDiscount} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Rule Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Bulk Tier 100+ Seats"
                  value={discountForm.name}
                  onChange={(e) => setDiscountForm({ ...discountForm, name: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Discount Value (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={discountForm.value}
                    onChange={(e) => setDiscountForm({ ...discountForm, value: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Min Seats</label>
                  <input
                    type="number"
                    required
                    value={discountForm.min_seats}
                    onChange={(e) => setDiscountForm({ ...discountForm, min_seats: Number(e.target.value) })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
                  />
                </div>
              </div>
              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="adminAppReq"
                  checked={discountForm.requires_admin_approval}
                  onChange={(e) => setDiscountForm({ ...discountForm, requires_admin_approval: e.target.checked })}
                  className="rounded text-blue-600"
                />
                <label htmlFor="adminAppReq" className="text-slate-700">Requires Executive Admin Approval</label>
              </div>
              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setShowDiscountModal(false)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Cancel</button>
                <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700">Save Rule</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showStaffModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <h3 className="text-sm font-semibold text-slate-900">Provision Staff Account</h3>
            <form onSubmit={handleCreateStaff} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={staffForm.full_name}
                  onChange={(e) => setStaffForm({ ...staffForm, full_name: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-medium mb-1">Corporate Email</label>
                <input
                  type="email"
                  required
                  value={staffForm.email}
                  onChange={(e) => setStaffForm({ ...staffForm, email: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-medium mb-1">Temporary Password</label>
                <input
                  type="password"
                  required
                  value={staffForm.password}
                  onChange={(e) => setStaffForm({ ...staffForm, password: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Staff Role</label>
                  <select
                    value={staffForm.staff_role}
                    onChange={(e) => setStaffForm({ ...staffForm, staff_role: e.target.value as 'sales' | 'finance' })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
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
                    placeholder="e.g. Enterprise Sales"
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setShowStaffModal(false)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Cancel</button>
                <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700">Provision Staff</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Ingest Bank Feed Item */}
      {showIngestModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Ingest Bank Statement Feed</h3>
                <p className="text-xs text-slate-500">Simulate bank statement line ingestion with automated reference matching.</p>
              </div>
              <button onClick={() => setShowIngestModal(false)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            <form onSubmit={handleIngestBankFeed} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Transaction ID (Reference) *</label>
                <input
                  type="text"
                  required
                  value={ingestForm.transaction_id}
                  onChange={(e) => setIngestForm({ ...ingestForm, transaction_id: e.target.value })}
                  placeholder="e.g. TX-CITI-998811"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Credit Amount (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={ingestForm.amount}
                    onChange={(e) => setIngestForm({ ...ingestForm, amount: e.target.value })}
                    placeholder="50000.00"
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Bank Account</label>
                  <input
                    type="text"
                    value={ingestForm.bank_account_number}
                    onChange={(e) => setIngestForm({ ...ingestForm, bank_account_number: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Raw Narration *</label>
                <textarea
                  rows={2}
                  required
                  value={ingestForm.raw_narration}
                  onChange={(e) => setIngestForm({ ...ingestForm, raw_narration: e.target.value })}
                  placeholder="e.g. NEFT CR-HDFC001-ACME CORP-INV-2026-0001-SETTLEMENT"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded font-mono text-[11px]"
                />
                <span className="text-[10px] text-slate-400">Include invoice pattern (e.g. INV-2026-0001) for auto-match confidence.</span>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Sender Entity Name</label>
                <input
                  type="text"
                  value={ingestForm.sender_name}
                  onChange={(e) => setIngestForm({ ...ingestForm, sender_name: e.target.value })}
                  placeholder="e.g. Acme Corporation Pvt Ltd"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setShowIngestModal(false)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Cancel</button>
                <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700">Ingest Transaction</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Confirm Match */}
      {confirmMatchModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Confirm Reconciliation Match</h3>
                <p className="text-xs text-slate-500">Record a realized payment and allocate credit to target invoice.</p>
              </div>
              <button onClick={() => setConfirmMatchModal(null)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-500">Bank Transaction ID:</span>
                <span className="font-mono font-bold text-slate-900">{confirmMatchModal.item.transaction_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Amount:</span>
                <span className="font-bold text-emerald-700">₹{parseFloat(confirmMatchModal.item.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Narration:</span>
                <span className="font-mono text-[11px] text-slate-700 truncate max-w-xs">{confirmMatchModal.item.raw_narration}</span>
              </div>
            </div>

            <form onSubmit={handleConfirmMatch} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Target Invoice *</label>
                <select
                  required
                  value={confirmMatchModal.invoice_id}
                  onChange={(e) => {
                    const invId = Number(e.target.value);
                    const inv = invoicesList.find(i => i.id === invId);
                    const alloc = inv ? Math.min(parseFloat(confirmMatchModal.item.amount), parseFloat(inv.remaining_balance)).toFixed(2) : confirmMatchModal.item.amount;
                    setConfirmMatchModal({
                      ...confirmMatchModal,
                      invoice_id: invId,
                      amount: alloc
                    });
                  }}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded bg-white text-xs"
                >
                  <option value={0}>-- Select Open Invoice --</option>
                  {invoicesList.filter(i => i.status !== 'paid' && i.status !== 'cancelled').map(inv => {
                    const b = customerBusinesses.find(cb => cb.id === inv.business_id);
                    return (
                      <option key={inv.id} value={inv.id}>
                        {inv.invoice_number} • {b?.company_name || 'Customer'} • Bal: ₹{parseFloat(inv.remaining_balance).toLocaleString('en-IN')}
                      </option>
                    );
                  })}
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Allocated Amount (₹) *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={confirmMatchModal.amount}
                  onChange={(e) => setConfirmMatchModal({ ...confirmMatchModal, amount: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Audit Notes</label>
                <input
                  type="text"
                  value={confirmMatchModal.notes}
                  onChange={(e) => setConfirmMatchModal({ ...confirmMatchModal, notes: e.target.value })}
                  placeholder="e.g. Bank credit slip verified against remittance advice"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setConfirmMatchModal(null)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Cancel</button>
                <button type="submit" className="px-3 py-1.5 bg-emerald-600 text-white rounded font-medium hover:bg-emerald-700">Post Realized Payment</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Dispute Transaction */}
      {disputeModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Flag Transaction for Dispute</h3>
                <p className="text-xs text-slate-500">Record reason why bank feed item could not be assigned to an invoice.</p>
              </div>
              <button onClick={() => setDisputeModal(null)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            <form onSubmit={handleDispute} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Dispute Reason *</label>
                <textarea
                  rows={3}
                  required
                  value={disputeModal.reason}
                  onChange={(e) => setDisputeModal({ ...disputeModal, reason: e.target.value })}
                  placeholder="e.g. Sender unknown; amount does not match any open quotation or invoice."
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setDisputeModal(null)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Cancel</button>
                <button type="submit" className="px-3 py-1.5 bg-red-600 text-white rounded font-medium hover:bg-red-700">Confirm Dispute</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Run Reminder Sweep */}
      {showSweepModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Execute Automated Reminder Sweep</h3>
                <p className="text-xs text-slate-500">Evaluates active dunning rules (-3 days, 0 due date, 7 days overdue, 14 days overdue).</p>
              </div>
              <button onClick={() => setShowSweepModal(false)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Simulated Evaluation Date (Optional)</label>
                <input
                  type="date"
                  value={sweepTargetDate}
                  onChange={(e) => setSweepTargetDate(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded font-mono"
                />
                <span className="text-[10px] text-slate-400 block mt-1">Leave empty to run against current system time.</span>
              </div>

              {sweepResult && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-emerald-800 space-y-1">
                  <div className="font-bold flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Sweep Completed Successfully</span>
                  </div>
                  <div className="text-[11px] grid grid-cols-3 gap-2 pt-1 font-mono">
                    <div>Evaluated: {sweepResult.processed_invoices}</div>
                    <div>Sent: {sweepResult.reminders_sent}</div>
                    <div>Skipped: {sweepResult.skipped_count}</div>
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setShowSweepModal(false)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Close</button>
                <button type="button" onClick={handleRunSweep} className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 flex items-center space-x-1">
                  <Play className="w-3 h-3" />
                  <span>Execute Sweep</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Create Reminder Rule */}
      {showRuleModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4 text-xs">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Configure Reminder Governance Rule</h3>
                <p className="text-xs text-slate-500">Configure schedule offsets and notification templates for commercial dunning.</p>
              </div>
              <button onClick={() => setShowRuleModal(false)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>

            <form onSubmit={handleCreateReminderRule} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Rule Name *</label>
                <input
                  type="text"
                  required
                  value={ruleForm.name}
                  onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })}
                  placeholder="e.g. Courtesy Notice (5 Days Before Due)"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Trigger Type *</label>
                  <select
                    value={ruleForm.trigger_type}
                    onChange={(e) => setRuleForm({ ...ruleForm, trigger_type: e.target.value as any })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded bg-white text-xs"
                  >
                    <option value="before_due">Before Due Date</option>
                    <option value="on_due">On Due Date</option>
                    <option value="after_due_overdue">After Due Date (Overdue)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Days Offset *</label>
                  <input
                    type="number"
                    required
                    value={ruleForm.days_offset}
                    onChange={(e) => setRuleForm({ ...ruleForm, days_offset: Number(e.target.value) })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded"
                  />
                  <span className="text-[10px] text-slate-400">e.g. -3 for 3 days before</span>
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Escalation *</label>
                  <select
                    value={ruleForm.escalation_level}
                    onChange={(e) => setRuleForm({ ...ruleForm, escalation_level: e.target.value as any })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded bg-white text-xs"
                  >
                    <option value="standard">Standard</option>
                    <option value="urgent">Urgent</option>
                    <option value="final_notice">Final Notice</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Subject Template *</label>
                <input
                  type="text"
                  required
                  value={ruleForm.subject_template}
                  onChange={(e) => setRuleForm({ ...ruleForm, subject_template: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Body Template *</label>
                <textarea
                  rows={3}
                  required
                  value={ruleForm.body_template}
                  onChange={(e) => setRuleForm({ ...ruleForm, body_template: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded"
                />
                <span className="text-[10px] text-slate-400">Variables: {'{invoice_number}'}, {'{business_name}'}, {'{amount_due}'}, {'{due_date}'}</span>
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button type="button" onClick={() => setShowRuleModal(false)} className="px-3 py-1.5 border border-slate-300 rounded text-slate-700">Cancel</button>
                <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700">Save Rule</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
