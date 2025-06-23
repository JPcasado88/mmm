import React, { useState, useEffect } from 'react';
import { format, subDays } from 'date-fns';
import {
  LineChart, Line, AreaChart, Area, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import api, { ChannelPerformance as ChannelPerformanceData } from '../services/api';
import { FiTrendingUp, FiAlertCircle, FiDollarSign } from 'react-icons/fi';

const CHANNELS = ['Google Ads', 'Meta Ads', 'Email', 'TikTok', 'Affiliate'];

function ChannelPerformance() {
  const [selectedChannel, setSelectedChannel] = useState('Google Ads');
  const [channelData, setChannelData] = useState<ChannelPerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange] = useState({
    start: format(subDays(new Date(), 90), 'yyyy-MM-dd'),
    end: format(subDays(new Date(), 1), 'yyyy-MM-dd'), // Use yesterday as end date
  });

  useEffect(() => {
    fetchChannelData();
  }, [selectedChannel, dateRange]);

  const fetchChannelData = async () => {
    try {
      setLoading(true);
      const data = await api.getChannelPerformance(selectedChannel, dateRange.start, dateRange.end);
      
      // Check if data contains an error
      if ('error' in data) {
        console.error('No data available:', data.error);
        setChannelData(null);
      } else {
        setChannelData(data);
      }
    } catch (error) {
      console.error('Error fetching channel data:', error);
      setChannelData(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!channelData) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Channel Performance Analysis</h1>
          <p className="text-gray-600 mt-1">
            Deep dive into channel-specific metrics and optimization opportunities
          </p>
        </div>

        {/* Channel Selector */}
        <div className="bg-white p-4 rounded-lg shadow">
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Channel</label>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            {CHANNELS.map((channel) => (
              <button
                key={channel}
                onClick={() => setSelectedChannel(channel)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  selectedChannel === channel
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {channel}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <p className="text-yellow-800 font-medium">No data available for {selectedChannel}</p>
          <p className="text-yellow-600 text-sm mt-2">
            This is a demo version. To see sample data, you would need to import marketing data for this channel.
          </p>
        </div>
      </div>
    );
  }

  const { metrics, time_series, best_performing_days } = channelData;

  // Prepare data for diminishing returns curve
  const roiCurveData = time_series.daily.map(day => ({
    spend: day.spend,
    revenue: day.revenue,
    roas: day.revenue / day.spend,
  })).sort((a, b) => a.spend - b.spend);

  // Format time series data for charts
  const timeSeriesData = time_series.daily.map(day => ({
    ...day,
    date: format(new Date(day.date), 'MMM dd'),
    roas: day.revenue / day.spend,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Channel Performance Analysis</h1>
        <p className="text-gray-600 mt-1">
          Deep dive into channel-specific metrics and optimization opportunities
        </p>
      </div>

      {/* Channel Selector */}
      <div className="bg-white p-4 rounded-lg shadow">
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Channel</label>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {CHANNELS.map((channel) => (
            <button
              key={channel}
              onClick={() => setSelectedChannel(channel)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedChannel === channel
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {channel}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Spend</p>
              <p className="text-2xl font-semibold">${(metrics.total_spend / 1000).toFixed(0)}K</p>
            </div>
            <FiDollarSign className="h-8 w-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Revenue</p>
              <p className="text-2xl font-semibold">${(metrics.total_revenue / 1000).toFixed(0)}K</p>
            </div>
            <FiTrendingUp className="h-8 w-8 text-green-400" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">ROAS</p>
              <p className="text-2xl font-semibold">{metrics.roas.toFixed(2)}x</p>
            </div>
            <div className={`p-2 rounded-full ${metrics.roas >= 4 ? 'bg-green-100' : 'bg-yellow-100'}`}>
              <FiTrendingUp className={`h-6 w-6 ${metrics.roas >= 4 ? 'text-green-600' : 'text-yellow-600'}`} />
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Optimization</p>
              <p className="text-lg font-semibold">{metrics.opportunity}</p>
            </div>
            <FiAlertCircle className="h-8 w-8 text-orange-400" />
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Spend vs Revenue Over Time */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Spend vs Revenue Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value: any) => `$${value.toLocaleString()}`} />
              <Legend />
              <Line type="monotone" dataKey="spend" stroke="#8884d8" name="Spend" />
              <Line type="monotone" dataKey="revenue" stroke="#82ca9d" name="Revenue" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* ROI Curve (Diminishing Returns) */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Diminishing Returns Analysis</h3>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="spend" name="Daily Spend" unit="$" />
              <YAxis dataKey="roas" name="ROAS" unit="x" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="ROAS by Spend" data={roiCurveData} fill="#8884d8" />
              {/* Add optimal spend line */}
              <Line
                type="monotone"
                dataKey="roas"
                stroke="#ff7300"
                strokeDasharray="5 5"
                name="Optimal Spend"
                data={[
                  { spend: metrics.optimal_daily_spend, roas: 0 },
                  { spend: metrics.optimal_daily_spend, roas: 10 },
                ]}
              />
            </ScatterChart>
          </ResponsiveContainer>
          <div className="mt-4 p-4 bg-blue-50 rounded-md">
            <p className="text-sm text-blue-800">
              <strong>Optimal Daily Spend:</strong> ${metrics.optimal_daily_spend.toLocaleString()}
              <br />
              <strong>Current Daily Spend:</strong> ${metrics.current_daily_spend.toLocaleString()}
              <br />
              <strong>Recommendation:</strong> {metrics.opportunity}
            </p>
          </div>
        </div>
      </div>

      {/* ROAS Over Time */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">ROAS Trend</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={timeSeriesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip formatter={(value: any) => `${value.toFixed(2)}x`} />
            <Area type="monotone" dataKey="roas" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Best Performing Days */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Best Performing Days</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ROAS
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Revenue
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {best_performing_days.map((day, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {format(new Date(day.date), 'MMM dd, yyyy')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                      {day.roas.toFixed(2)}x
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${day.revenue.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default ChannelPerformance;