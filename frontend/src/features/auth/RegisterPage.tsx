import React, { useState } from 'react';
import { api } from '../../services/api';
import { Building, ArrowLeft } from 'lucide-react';

interface RegisterPageProps {
  onRegisterSuccess: () => void;
  onNavigateLogin: () => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onRegisterSuccess, onNavigateLogin }) => {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    company_name: '',
    tax_id: '',
    billing_address: '',
    billing_city: '',
    billing_state: '',
    billing_postal_code: '',
    billing_country: 'India',
    contact_phone: '',
  });

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    try {
      await api.registerCustomer(formData);
      onRegisterSuccess();
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration failed. Please check your information.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center py-10 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-xl text-center">
        <div className="inline-flex w-11 h-11 bg-slate-900 rounded-lg items-center justify-center text-white font-bold text-xl shadow-sm mb-2">
          B
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Customer Business Registration
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Create an organization account on Brightloop SMS to manage subscriptions and invoices.
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-sm border border-slate-200 rounded-lg">
          {errorMessage && (
            <div className="mb-5 p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700">
              {errorMessage}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="border-b border-slate-200 pb-3 mb-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                Business Organization Details
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-slate-700 mb-1">Company Legal Name *</label>
                  <input
                    type="text"
                    name="company_name"
                    required
                    value={formData.company_name}
                    onChange={handleChange}
                    placeholder="e.g. Acme Technologies Pvt Ltd"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Tax ID / GSTIN</label>
                  <input
                    type="text"
                    name="tax_id"
                    value={formData.tax_id}
                    onChange={handleChange}
                    placeholder="e.g. 29ABCDE1234F1Z5"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Billing Phone</label>
                  <input
                    type="text"
                    name="contact_phone"
                    value={formData.contact_phone}
                    onChange={handleChange}
                    placeholder="+91 98765 43210"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-slate-700 mb-1">Billing Street Address</label>
                  <input
                    type="text"
                    name="billing_address"
                    value={formData.billing_address}
                    onChange={handleChange}
                    placeholder="Street, Building, Area"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">City</label>
                  <input
                    type="text"
                    name="billing_city"
                    value={formData.billing_city}
                    onChange={handleChange}
                    placeholder="e.g. Bengaluru"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Postal Code</label>
                  <input
                    type="text"
                    name="billing_postal_code"
                    value={formData.billing_postal_code}
                    onChange={handleChange}
                    placeholder="560103"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>
              </div>
            </div>

            <div className="border-b border-slate-200 pb-3 mb-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                Business Owner Account (Primary Administrator)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-slate-700 mb-1">Full Name *</label>
                  <input
                    type="text"
                    name="full_name"
                    required
                    value={formData.full_name}
                    onChange={handleChange}
                    placeholder="Your legal name"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-slate-700 mb-1">Official Email Address *</label>
                  <input
                    type="email"
                    name="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="owner@company.com"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-slate-700 mb-1">Password (Min. 8 characters) *</label>
                  <input
                    type="password"
                    name="password"
                    required
                    minLength={8}
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Choose a strong password"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 transition-colors shadow-sm"
            >
              {isLoading ? 'Creating Business Account...' : 'Complete Business Registration'}
            </button>
          </form>

          <div className="mt-5 pt-4 border-t border-slate-100 text-center">
            <button
              type="button"
              onClick={onNavigateLogin}
              className="inline-flex items-center space-x-1.5 text-xs text-slate-600 hover:text-slate-900 font-medium"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Sign In</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

