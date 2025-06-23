import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import api, { OptimizationResult, DimishingReturnsData } from '../services/api';
import { FiDollarSign, FiTrendingUp, FiAlertTriangle, FiCheck } from 'react-icons/fi';

const COLORS = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444'];

interface ChannelBudget {
  channel: string;
  current: number;
  optimized: number;
  min?: number;
  max?: number;
}

function BudgetOptimizer() {
  const [totalBudget, setTotalBudget] = useState(13000); // Daily budget
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [diminishingReturns, setDiminishingReturns] = useState<DimishingReturnsData | null>(null);
  const [channelBudgets, setChannelBudgets] = useState<ChannelBudget[]>([]);
  const [loading, setLoading] = useState(false);
  const [simulationMode, setSimulationMode] = useState(false);
  const [customBudgets, setCustomBudgets] = useState<Record<string, number>>({});

  useEffect(() => {
    fetchDiminishingReturns();
    runOptimization();
  }, []);

  const fetchDiminishingReturns = async () => {
    try {
      const data = await api.getDiminishingReturns();
      setDiminishingReturns(data);
    } catch (error) {
      console.error('Error fetching diminishing returns:', error);
    }
  };

  const runOptimization = async () => {
    try {
      setLoading(true);
      const result = await api.optimizeBudget(totalBudget);
      setOptimizationResult(result);
      
      // Initialize channel budgets
      const budgets: ChannelBudget[] = Object.keys(result.optimized_allocation).map(channel => ({
        channel,
        current: result.recommendations.find(r => r.channel === channel)?.current_spend || 0,
        optimized: result.optimized_allocation[channel],
      }));
      setChannelBudgets(budgets);
      setCustomBudgets(result.optimized_allocation);
    } catch (error) {
      console.error('Error running optimization:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBudgetChange = (channel: string, value: number) => {
    setCustomBudgets(prev => ({
      ...prev,
      [channel]: value
    }));
  };

  const calculateProjectedRevenue = () => {
    if (!optimizationResult || !diminishingReturns) return 0;
    
    let projectedRevenue = 0;
    Object.entries(customBudgets).forEach(([channel, spend]) => {
      const channelData = diminishingReturns[channel];
      if (channelData) {
        // Simple linear interpolation based on efficiency
        const efficiency = channelData.efficiency_status === 'efficient' ? 5.5 : 
                          channelData.efficiency_status === 'under-invested' ? 6.5 : 
                          channelData.efficiency_status === 'over-saturated' ? 3.5 : 4.5;
        projectedRevenue += spend * efficiency;
      }
    });
    
    return projectedRevenue;
  };

  if (loading || !optimizationResult) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading optimization results...</div>
      </div>
    );
  }

  const comparisonData = channelBudgets.map(budget => ({
    channel: budget.channel,
    current: budget.current,
    optimized: simulationMode ? customBudgets[budget.channel] : budget.optimized,
    difference: (simulationMode ? customBudgets[budget.channel] : budget.optimized) - budget.current,
  }));

  const projectedRevenue = simulationMode ? calculateProjectedRevenue() : optimizationResult.projected_revenue;
  const revenueLift = projectedRevenue - optimizationResult.current_revenue;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Budget Optimization</h1>
        <p className="text-gray-600 mt-1">
          Optimize your marketing budget allocation for maximum ROI
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Daily Budget</p>
              <p className="text-2xl font-semibold">${totalBudget.toLocaleString()}</p>
            </div>
            <FiDollarSign className="h-8 w-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Current Revenue</p>
              <p className="text-2xl font-semibold">${optimizationResult.current_revenue.toLocaleString()}</p>
            </div>
            <FiTrendingUp className="h-8 w-8 text-blue-400" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Projected Revenue</p>
              <p className="text-2xl font-semibold">${projectedRevenue.toLocaleString()}</p>
            </div>
            <FiTrendingUp className="h-8 w-8 text-green-400" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Revenue Lift</p>
              <p className="text-2xl font-semibold text-green-600">+${revenueLift.toLocaleString()}</p>
              <p className="text-xs text-gray-500 mt-1">+{optimizationResult.roi_improvement}% ROI</p>
            </div>
            <div className="p-2 bg-green-100 rounded-full">
              <FiCheck className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Budget Comparison Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Budget Allocation Comparison</h3>
          <button
            onClick={() => setSimulationMode(!simulationMode)}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              simulationMode
                ? 'bg-orange-100 text-orange-700'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            {simulationMode ? 'Simulation Mode' : 'View Optimized'}
          </button>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={comparisonData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="channel" />
            <YAxis />
            <Tooltip formatter={(value: any) => `$${value.toLocaleString()}`} />
            <Legend />
            <Bar dataKey="current" fill="#94A3B8" name="Current Spend" />
            <Bar dataKey="optimized" fill="#3B82F6" name={simulationMode ? "Simulated" : "Optimized Spend"} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Interactive Budget Simulator */}
      {simulationMode && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Budget Simulator</h3>
          <div className="space-y-4">
            {channelBudgets.map((budget) => (
              <div key={budget.channel} className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium text-gray-700">{budget.channel}</label>
                  <span className="text-sm text-gray-500">${customBudgets[budget.channel]?.toLocaleString()}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max={totalBudget * 0.5}
                  value={customBudgets[budget.channel] || 0}
                  onChange={(e) => handleBudgetChange(budget.channel, Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>$0</span>
                  <span>${(totalBudget * 0.5).toLocaleString()}</span>
                </div>
              </div>
            ))}
            <div className="pt-4 border-t">
              <div className="flex justify-between items-center">
                <span className="font-medium">Total Allocated:</span>
                <span className={`font-bold ${
                  Object.values(customBudgets).reduce((a, b) => a + b, 0) > totalBudget
                    ? 'text-red-600'
                    : 'text-green-600'
                }`}>
                  ${Object.values(customBudgets).reduce((a, b) => a + b, 0).toLocaleString()} / ${totalBudget.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Optimization Recommendations</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {optimizationResult.recommendations.map((rec, index) => (
            <div key={index} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  {rec.action === 'increase' ? (
                    <FiTrendingUp className="h-5 w-5 text-green-500 mr-3" />
                  ) : (
                    <FiAlertTriangle className="h-5 w-5 text-orange-500 mr-3" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-gray-900">{rec.message}</p>
                    <p className="text-sm text-gray-500">
                      Current: ${rec.current_spend.toLocaleString()} → Recommended: ${rec.recommended_spend.toLocaleString()}
                    </p>
                  </div>
                </div>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  rec.priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {rec.priority} priority
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Diminishing Returns Analysis */}
      {diminishingReturns && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Channel Efficiency Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(diminishingReturns).map(([channel, data]) => (
              <div key={channel} className="border rounded-lg p-4">
                <h4 className="font-medium text-gray-900">{channel}</h4>
                <div className="mt-2 space-y-1">
                  <p className="text-sm text-gray-600">
                    Status: <span className={`font-medium ${
                      data.efficiency_status === 'efficient' ? 'text-green-600' :
                      data.efficiency_status === 'under-invested' ? 'text-blue-600' :
                      data.efficiency_status === 'over-saturated' ? 'text-red-600' :
                      'text-yellow-600'
                    }`}>{data.efficiency_status}</span>
                  </p>
                  <p className="text-sm text-gray-600">
                    Current: ${data.current_spend.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600">
                    Saturation: ${data.saturation_point.toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default BudgetOptimizer;