"use client";

import { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const COLORS = [
  "#0088FE",
  "#00C49F",
  "#FFBB28",
  "#FF8042",
  "#8884D8",
  "#82ca9d",
  "#ffc658",
  "#ff7c7c",
  "#8dd1e1",
  "#d084d0",
];

interface TokenData {
  prompt: number;
  completion: number;
  total: number;
}

interface Query {
  model_provider: string;
  model_used: string;
  tokens: TokenData;
  timestamp: string;
}

interface AggregatedData {
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  model_usage_count: { [key: string]: number };
  provider_stats: {
    [key: string]: { prompt: number; completion: number; total: number };
  };
  model_stats: {
    [key: string]: { prompt: number; completion: number; total: number };
  };
  model_avg_latency?: { [key: string]: number };
}

interface ApiResponse {
  queries: Query[];
  filters: {
    providers: string[];
    models: string[];
  };
  aggregated: AggregatedData;
}

export default function TokensPage() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");

  useEffect(() => {
    fetchData();
  }, [selectedProvider, selectedModel]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const params = new URLSearchParams();
      if (selectedProvider) params.append("model_provider", selectedProvider);
      if (selectedModel) params.append("model_used", selectedModel);

      const response = await fetch(
        `${backendUrl}/tokens/data?${params.toString()}`
      );
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error("Error fetching token data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleResetFilters = () => {
    setSelectedProvider("");
    setSelectedModel("");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-xl text-gray-600">Loading token data...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-xl text-gray-600">No data available</div>
      </div>
    );
  }

  // Prepare data for charts
  const providerChartData = Object.entries(data.aggregated.provider_stats).map(
    ([provider, stats]) => ({
      name: provider,
      prompt: stats.prompt,
      completion: stats.completion,
      total: stats.total,
    })
  );

  const modelChartData = Object.entries(data.aggregated.model_stats).map(
    ([model, stats]) => ({
      name: model,
      prompt: stats.prompt,
      completion: stats.completion,
      total: stats.total,
    })
  );

  const modelUsageData = Object.entries(
    data.aggregated.model_usage_count
  ).map(([model, count]) => ({
    name: model,
    count,
  }));

  const tokenTypeData = [
    { name: "Prompt Tokens", value: data.aggregated.total_prompt_tokens },
    {
      name: "Completion Tokens",
      value: data.aggregated.total_completion_tokens,
    },
  ];

  // Prepare latency data if available
  const modelLatencyData = data.aggregated.model_avg_latency
    ? Object.entries(data.aggregated.model_avg_latency).map(
        ([model, avgLatency]) => ({
          name: model,
          latency: Math.round(avgLatency),
        })
      )
    : [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Token Usage Analytics
          </h1>
          <p className="text-gray-600">
            Monitor and analyze token consumption across different models and
            providers
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Filters</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Provider
              </label>
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Providers</option>
                {data.filters.providers.map((provider) => (
                  <option key={provider} value={provider}>
                    {provider}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Model
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Models</option>
                {data.filters.models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={handleResetFilters}
                className="w-full px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                Reset Filters
              </button>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">
              Total Prompt Tokens
            </h3>
            <p className="text-3xl font-bold text-blue-600">
              {data.aggregated.total_prompt_tokens.toLocaleString()}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">
              Total Completion Tokens
            </h3>
            <p className="text-3xl font-bold text-green-600">
              {data.aggregated.total_completion_tokens.toLocaleString()}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">
              Total Tokens
            </h3>
            <p className="text-3xl font-bold text-purple-600">
              {data.aggregated.total_tokens.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Token Type Distribution - Pie Chart */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Token Type Distribution
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={tokenTypeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(props: any) =>
                  `${props.name}: ${(props.percent * 100).toFixed(0)}%`
                }
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {tokenTypeData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Token Usage by Provider */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Token Usage by Provider
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={providerChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="prompt" fill="#0088FE" name="Prompt Tokens" />
              <Bar
                dataKey="completion"
                fill="#00C49F"
                name="Completion Tokens"
              />
              <Bar dataKey="total" fill="#FFBB28" name="Total Tokens" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Token Usage by Model */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Token Usage by Model
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={modelChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="prompt" fill="#8884D8" name="Prompt Tokens" />
              <Bar
                dataKey="completion"
                fill="#82ca9d"
                name="Completion Tokens"
              />
              <Bar dataKey="total" fill="#ffc658" name="Total Tokens" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Model Usage Frequency */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Model Usage Frequency
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={modelUsageData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar
                dataKey="count"
                fill="#FF8042"
                name="Number of API Calls"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Average Latency by Model */}
        {modelLatencyData.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Average Latency by Model
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={modelLatencyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey="latency"
                  fill="#8B5CF6"
                  name="Average Latency (ms)"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Back to Home Button */}
        <div className="text-center">
          <a
            href="/"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Home
          </a>
        </div>
      </div>
    </div>
  );
}
