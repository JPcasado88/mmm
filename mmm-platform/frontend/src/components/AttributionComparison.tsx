import React, { useState, useEffect } from 'react';
import { format, subDays } from 'date-fns';
import {
  BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import api, { AttributionModel, AttributionResult } from '../services/api';
import { FiInfo, FiPercent } from 'react-icons/fi';

const COLORS = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444'];

interface ComparisonData {
  models: Record<string, AttributionResult[]>;
  channel_variance: Record<string, {
    min: number;
    max: number;
    variance: number;
    mean: number;
  }>;
  recommendation: string;
}

function AttributionComparison() {
  const [attributionModels, setAttributionModels] = useState<AttributionModel[]>([]);
  const [selectedModel, setSelectedModel] = useState('linear');
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange] = useState({
    start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd'),
  });

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch available models
      const modelsResponse = await api.getAttributionModels();
      setAttributionModels(modelsResponse.models);
      
      // Fetch comparison data
      const comparison = await api.compareAttributionModels(dateRange.start, dateRange.end);
      setComparisonData(comparison);
    } catch (error) {
      console.error('Error fetching attribution data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !comparisonData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading attribution analysis...</div>
      </div>
    );
  }

  // Prepare data for visualization
  const channelData = Object.keys(comparisonData.channel_variance).map(channel => {
    const modelData: any = { channel };
    Object.entries(comparisonData.models).forEach(([model, results]) => {
      const channelResult = results.find(r => r.channel === channel);
      modelData[model] = channelResult?.percentage || 0;
    });
    return modelData;
  });

  // Prepare radar chart data
  const radarData = Object.keys(comparisonData.channel_variance).map(channel => ({
    channel,
    value: comparisonData.models[selectedModel]?.find(r => r.channel === channel)?.percentage || 0,
  }));

  // Calculate model differences
  const modelDifferences = Object.entries(comparisonData.models).map(([model, results]) => {
    const totalRevenue = results.reduce((sum, r) => sum + r.attributed_revenue, 0);
    return {
      model,
      totalRevenue,
      results,
    };
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Attribution Model Comparison</h1>
        <p className="text-gray-600 mt-1">
          Compare different attribution models to understand channel contribution
        </p>
      </div>

      {/* Model Selector */}
      <div className="bg-white p-4 rounded-lg shadow">
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Primary Model</label>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {attributionModels.map((model) => (
            <button
              key={model.id}
              onClick={() => setSelectedModel(model.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedModel === model.id
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {model.name}
            </button>
          ))}
        </div>
      </div>

      {/* Model Descriptions */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
        <div className="flex">
          <FiInfo className="h-5 w-5 text-blue-400 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              {attributionModels.find(m => m.id === selectedModel)?.name} Model
            </h3>
            <p className="mt-1 text-sm text-blue-700">
              {attributionModels.find(m => m.id === selectedModel)?.description}
            </p>
          </div>
        </div>
      </div>

      {/* Comparison Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Channel Attribution by Model */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Channel Attribution by Model</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={channelData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="channel" />
              <YAxis label={{ value: 'Attribution %', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value: any) => `${value.toFixed(1)}%`} />
              <Legend />
              {Object.keys(comparisonData.models).map((model, index) => (
                <Bar key={model} dataKey={model} fill={COLORS[index % COLORS.length]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Selected Model Distribution */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {selectedModel.charAt(0).toUpperCase() + selectedModel.slice(1).replace('_', ' ')} Attribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="channel" />
              <PolarRadiusAxis angle={90} domain={[0, 'dataMax']} />
              <Radar name="Attribution %" dataKey="value" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.6} />
              <Tooltip formatter={(value: any) => `${value.toFixed(1)}%`} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Channel Variance Analysis */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Channel Attribution Variance</h3>
          <p className="text-sm text-gray-600 mt-1">How much attribution varies across different models</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Channel
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Min Attribution
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Max Attribution
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mean Attribution
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Variance
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.entries(comparisonData.channel_variance).map(([channel, variance]) => (
                <tr key={channel}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {channel}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {variance.min.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {variance.max.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {variance.mean.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      variance.variance < 5 ? 'bg-green-100 text-green-800' :
                      variance.variance < 15 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {variance.variance.toFixed(1)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Recommendation */}
      <div className="bg-green-50 border-l-4 border-green-400 p-4">
        <div className="flex">
          <FiPercent className="h-5 w-5 text-green-400 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-green-800">Model Recommendation</h3>
            <p className="mt-1 text-sm text-green-700">
              {comparisonData.recommendation}
            </p>
          </div>
        </div>
      </div>

      {/* Revenue Attribution Details */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Revenue Attribution by Model</h3>
        <div className="space-y-4">
          {modelDifferences.map(({ model, totalRevenue, results }) => (
            <div key={model} className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <h4 className="font-medium text-gray-900">
                  {model.charAt(0).toUpperCase() + model.slice(1).replace('_', ' ')}
                </h4>
                <span className="text-sm text-gray-600">
                  Total: ${totalRevenue.toLocaleString()}
                </span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                {results.map((result, index) => (
                  <div key={result.channel} className="text-center">
                    <div
                      className="h-2 rounded-full mb-1"
                      style={{
                        backgroundColor: COLORS[index % COLORS.length],
                        width: `${result.percentage}%`,
                        minWidth: '20px'
                      }}
                    />
                    <p className="text-xs text-gray-600">{result.channel}</p>
                    <p className="text-xs font-medium">${(result.attributed_revenue / 1000).toFixed(0)}K</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AttributionComparison;