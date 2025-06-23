import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import ChannelPerformance from './components/ChannelPerformance';
import BudgetOptimizer from './components/BudgetOptimizer';
import AttributionComparison from './components/AttributionComparison';
import { FiHome, FiTrendingUp, FiDollarSign, FiPieChart } from 'react-icons/fi';

function Navigation() {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: FiHome },
    { path: '/channels', label: 'Channel Performance', icon: FiTrendingUp },
    { path: '/optimize', label: 'Budget Optimizer', icon: FiDollarSign },
    { path: '/attribution', label: 'Attribution', icon: FiPieChart },
  ];

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">MMM Platform</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isActive
                        ? 'border-primary-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    <Icon className="mr-2" size={16} />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/channels" element={<ChannelPerformance />} />
            <Route path="/optimize" element={<BudgetOptimizer />} />
            <Route path="/attribution" element={<AttributionComparison />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;