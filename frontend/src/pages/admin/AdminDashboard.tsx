import {
  TrendingDown,
  Users,
  DollarSign,
  Smartphone,
  AlertCircle,
  Upload,
} from "lucide-react";
import { useState, useEffect } from "react";
import { Button } from "../../components/ui/button";
import UploadModel from "../../components/Layout/UploadModel";

export const AdminDashboard = () => {
  const [isAdmin] = useState(true);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // 🔹 Dynamic data states
  const [stats, setStats] = useState<any[]>([]);
  const [recentSales, setRecentSales] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // 🔹 Model info states
  const [modelInfo, setModelInfo] = useState<any | null>(null);
  const [modelLoading, setModelLoading] = useState(true);

  // 🔹 Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/admin_dashboard");
        const data = await res.json();

        if (data.status === "success") {
          const records = data.dashboard_data || [];

          // Parse currency safely (₹, commas, etc.)
          const parsePrice = (val: any) => {
            if (!val) return 0;
            const str = String(val).replace(/[₹,]/g, "");
            return parseFloat(str) || 0;
          };

          // Calculate total revenue and items sold
          const totalRevenue = records.reduce(
            (sum: number, item: any) =>
              sum + parsePrice(item.Optimal_Price || item.ML_Predicted),
            0
          );

          const totalSold = records.length;

          setStats([
            {
              title: "Total Revenue",
              value: `₹${totalRevenue.toLocaleString()}`,
              change: "+12.5%",
              trend: "up",
              icon: DollarSign,
              color: "bg-green-500",
            },
            {
              title: "iPhones Sold",
              value: totalSold.toString(),
              change: "+8.2%",
              trend: "up",
              icon: Smartphone,
              color: "bg-blue-500",
            },
            {
              title: "Active Users",
              value: "12,847",
              change: "+5.1%",
              trend: "up",
              icon: Users,
              color: "bg-purple-500",
            },
            {
              title: "Conversion Rate",
              value: "3.47%",
              change: "-0.8%",
              trend: "down",
              icon: TrendingDown,
              color: "bg-orange-500",
            },
          ]);

          // 🔹 Recent predictions: show ML, Gemini, Current, Rating, etc.
          const dynamicSales = records.map((item: any, i: number) => ({
            model: item.Model || "iPhone",
            source: item.Source || "Amazon",
            ml: item.ML_Predicted || "N/A",
            gemini: item.Gemini_Predicted || "N/A",
            current: item.Current_Price || "N/A",
            rating: item.Current_Rating || "N/A",
            optimal: item.Optimal_Price || "N/A",
            analysis: item.Analysis || "No analysis available",
            time: item.DateTime || "Recently",
          }));

          setRecentSales(dynamicSales);
        } else {
          console.error("Dashboard fetch failed:", data.message);
        }
      } catch (err) {
        console.error("Error fetching dashboard:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // 🔹 Fetch model info
  useEffect(() => {
    const fetchModelInfo = async () => {
      try {
        const res = await fetch("http://localhost:8000/admin/model-status");
        const data = await res.json();
        if (data.status && data.status.model_name) {
          setModelInfo(data.status);
        } else {
          setModelInfo(null);
        }
      } catch (err) {
        console.error("Error fetching model status:", err);
      } finally {
        setModelLoading(false);
      }
    };
    fetchModelInfo();
  }, []);

  // 🔄 Refresh button
  const handleRefresh = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/refresh_dashboard", {
        method: "POST",
      });
      const data = await res.json();
      alert(data.message || "Dashboard refreshed!");
      window.location.reload();
    } catch (error) {
      alert("Error refreshing dashboard!");
      console.error(error);
    }
  };

  // ----------------------------------
  return (
    <div className="p-6 space-y-8 bg-white text-black min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Dashboard Overview
          </h1>
          <p className="text-gray-600">
            Monitor your iPhone store performance and insights.
          </p>
        </div>
        <Button
          onClick={handleRefresh}
          className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-2 rounded-lg hover:shadow-lg transition-all"
        >
          🔄 Refresh Dashboard
        </Button>
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div
            key={index}
            className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="text-white" size={22} />
              </div>
              <span
                className={`text-sm font-medium ${
                  stat.trend === "up" ? "text-green-600" : "text-red-600"
                }`}
              >
                {stat.change}
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-1">
              {stat.value}
            </h3>
            <p className="text-sm text-gray-600">{stat.title}</p>
          </div>
        ))}
      </div>

      {/* Main Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Recent Sales & Predictions */}
        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Recent Sales & Predictions
          </h2>
          <div className="space-y-4">
            {loading ? (
              <p className="text-gray-500 text-center">Loading data...</p>
            ) : recentSales.length === 0 ? (
              <p className="text-gray-500 text-center">
                No records found yet.
              </p>
            ) : (
              recentSales.map((sale, index) => (
                <div
                  key={index}
                  className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-all"
                >
                  <div className="flex justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {sale.model} — {sale.source}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        🤖 ML: {sale.ml} | 🧠 Gemini: {sale.gemini}
                      </p>
                      <p className="text-sm text-gray-600">
                        💰 Current: {sale.current} | ⭐ {sale.rating}
                      </p>
                      <p className="text-sm text-gray-600">
                        ✅ Optimal: {sale.optimal}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        📈 {sale.analysis}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-gray-800 font-semibold">
                        {sale.optimal}
                      </p>
                      <p className="text-sm text-gray-500">{sale.time}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* AI Insights */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold flex items-center mb-4 text-gray-900">
            <AlertCircle className="h-5 w-5 mr-2 text-blue-500" />
            AI Insights
          </h2>
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
              <p className="text-sm font-medium text-blue-700 mb-1">
                Price Alert
              </p>
              <p className="text-sm text-blue-600">
                Price movement detected in latest predictions.
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="mt-2 text-blue-700 hover:text-blue-800"
              >
                View Details
              </Button>
            </div>

            <div className="p-4 bg-green-50 rounded-lg border border-green-100">
              <p className="text-sm font-medium text-green-700 mb-1">
                Opportunity
              </p>
              <p className="text-sm text-green-600">
                High potential demand detected. Adjust pricing strategy.
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="mt-2 text-green-700 hover:text-green-800"
              >
                Create Campaign
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Model Management */}
      <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          Model Management
        </h2>

        {modelLoading ? (
          <p className="text-gray-500">Loading model info...</p>
        ) : modelInfo ? (
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h3 className="font-medium text-gray-900">
                Current Model: {modelInfo.model_name}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Uploaded on: {modelInfo.uploaded_at}
              </p>
            </div>
            <div
              className={`px-3 py-1 text-sm font-medium rounded-full ${
                modelInfo.status === "active"
                  ? "bg-green-100 text-green-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              {modelInfo.status === "active" ? "Active" : "Inactive"}
            </div>
          </div>
        ) : (
          <p className="text-gray-500 mb-4">No model uploaded yet.</p>
        )}

        {isAdmin && (
          <div className="pt-4 border-t border-gray-200">
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium rounded-lg hover:shadow-lg transform hover:scale-105 transition-all"
            >
              <Upload className="w-5 h-5" />
              Upload Model
            </button>
            <UploadModel
              isOpen={isUploadModalOpen}
              onClose={() => setIsUploadModalOpen(false)}
              onSuccess={(msg) => {
                alert(msg);
                setIsUploadModalOpen(false);
                window.location.reload();
              }}
              onError={(msg) => alert(msg)}
              authToken="dummy-auth-token"
            />
            <p className="text-sm text-gray-500 mt-2">
              Upload a new trained model (.pkl or .joblib file)
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
