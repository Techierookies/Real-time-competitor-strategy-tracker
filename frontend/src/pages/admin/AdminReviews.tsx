import { useState, useEffect } from "react";
import { Check, X, Star, Trash2 } from "lucide-react";
import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { useToast } from "../../hooks/use-toast";

interface Review {
  source: string;
  rating: number;
  review: string;
}

export const AdminReviews = () => {
  const { toast } = useToast();
  const [statusFilter, setStatusFilter] = useState<"all" | "pending" | "approved" | "rejected">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [reviews, setReviews] = useState<(Review & { id: string; status: string; date: string })[]>([]);
  const [model, setModel] = useState("iPhone 16");

  // ✅ Fetch reviews dynamically from FastAPI
  useEffect(() => {
    const fetchReviews = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/synthetic-reviews/${model}`);
        const data = await res.json();
        if (data.status === "success") {
          // Adding fake IDs + default status for UI consistency
          const enhanced = data.reviews.map((r: Review, idx: number) => ({
            ...r,
            id: `${idx + 1}`,
            status: "approved",
            date: new Date().toISOString().split("T")[0],
          }));
          setReviews(enhanced);
        } else {
          toast({ title: "Error", description: data.message || "No reviews found." });
        }
      } catch (err) {
        toast({ title: "Error", description: "Failed to fetch reviews." });
      }
    };
    fetchReviews();
  }, [model]);

  const approveReview = (id: string) => {
    setReviews(reviews.map(r => r.id === id ? { ...r, status: "approved" } : r));
    toast({ title: "Review Approved", description: "The review has been approved successfully." });
  };

  const rejectReview = (id: string) => {
    setReviews(reviews.map(r => r.id === id ? { ...r, status: "rejected" } : r));
    toast({ title: "Review Rejected", description: "The review has been rejected." });
  };

  const deleteReview = (id: string) => {
    setReviews(reviews.filter(r => r.id !== id));
    toast({ title: "Review Deleted", description: "The review has been permanently deleted." });
  };

  const renderStars = (rating: number) => (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map(star => (
        <Star
          key={star}
          size={16}
          className={star <= rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"}
        />
      ))}
    </div>
  );

  const filteredReviews = reviews.filter(review => {
    const matchesSearch =
      review.review.toLowerCase().includes(searchQuery.toLowerCase()) ||
      review.source.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || review.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved":
        return "bg-green-100 text-green-700";
      case "rejected":
        return "bg-red-100 text-red-700";
      default:
        return "bg-yellow-100 text-yellow-700";
    }
  };

  return (
    <div className="space-y-6 bg-white text-black min-h-screen p-6 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold">Reviews</h1>
          <p className="text-gray-600 mt-1">Manage and moderate customer reviews</p>
        </div>

        {/* Filters */}
        <div className="flex gap-2 flex-wrap">
          {(["all", "pending", "approved", "rejected"] as const).map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                statusFilter === status
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Model Dropdown */}
      <div className="flex items-center gap-4">
        <label className="font-medium">Select Model:</label>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="p-2 border rounded-lg"
        >
          <option value="iPhone 15">iPhone 15</option>
          <option value="iPhone 16">iPhone 16</option>
          <option value="iPhone 17">iPhone 17</option>
        </select>
      </div>

      {/* Search */}
      <div>
        <input
          type="text"
          placeholder="Search by review or source..."
          className="w-full md:w-1/2 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Review Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredReviews.map((review) => (
          <Card
            key={review.id}
            className="p-6 border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow bg-white"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-lg">{review.source}</h3>
                <span
                  className={`inline-block mt-2 text-xs font-medium px-3 py-1 rounded-full ${getStatusColor(
                    review.status
                  )}`}
                >
                  {review.status}
                </span>
              </div>
              {renderStars(review.rating)}
            </div>

            <p className="text-gray-800 text-sm mb-4">{review.review}</p>
            <p className="text-xs text-gray-500 mb-4">Posted on {review.date}</p>

            <div className="flex gap-2">
              {review.status === "pending" && (
                <>
                  <Button
                    onClick={() => approveReview(review.id)}
                    className="flex-1 bg-green-100 text-green-700 hover:bg-green-200"
                  >
                    <Check size={16} className="mr-1" /> Approve
                  </Button>
                  <Button
                    onClick={() => rejectReview(review.id)}
                    className="flex-1 bg-red-100 text-red-700 hover:bg-red-200"
                  >
                    <X size={16} className="mr-1" /> Reject
                  </Button>
                </>
              )}
              <Button
                onClick={() => deleteReview(review.id)}
                className="flex-1 bg-gray-100 text-gray-700 hover:bg-gray-200"
              >
                <Trash2 size={16} className="mr-1" /> Delete
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
