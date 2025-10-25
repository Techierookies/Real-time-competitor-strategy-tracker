import { useState } from "react";
import { Check, X, Star, Trash2 } from "lucide-react";
import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { useToast } from "../../hooks/use-toast";

interface Review {
  id: string;
  product: string;
  customer: string;
  rating: number;
  comment: string;
  status: "pending" | "approved" | "rejected";
  date: string;
}

export const AdminReviews = () => {
  const { toast } = useToast();
  const [statusFilter, setStatusFilter] = useState<"all" | "pending" | "approved" | "rejected">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [reviews, setReviews] = useState<Review[]>([
    { id: "1", product: "iPhone 15 Pro Max", customer: "Amit Patel", rating: 5, comment: "Amazing phone! Best iPhone yet. Camera quality is incredible.", status: "approved", date: "2024-01-20" },
    { id: "2", product: "iPhone 15 Pro", customer: "Rajesh Kumar", rating: 4, comment: "Great device but a bit expensive. Love the titanium design.", status: "approved", date: "2024-01-19" },
    { id: "3", product: "iPhone 15", customer: "Priya SHarma", rating: 3, comment: "Good phone but expected more for the price.", status: "pending", date: "2024-01-18" },
    { id: "4", product: "iphone 16", customer: "Sneha Reddy", rating: 5, comment: "Best Phone ever! Camera Quality is perfect.", status: "approved", date: "2024-01-17" },
    { id: "5", product: "iPhone 14", customer: "Priyanshi Agarwal", rating: 1, comment: "Terrible product. Complete waste of money!!!", status: "pending", date: "2024-01-16" },
  ]);

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
      review.product.toLowerCase().includes(searchQuery.toLowerCase()) ||
      review.customer.toLowerCase().includes(searchQuery.toLowerCase());
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

      {/* Search */}
      <div>
        <input
          type="text"
          placeholder="Search by product or customer..."
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
                <h3 className="font-semibold text-lg">{review.product}</h3>
                <p className="text-sm text-gray-600">By {review.customer}</p>
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

            <p className="text-gray-800 text-sm mb-4">{review.comment}</p>
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
                <Trash2 size={16} className="mr-1 bg-red-100 text-red-700 hover:bg-red-200" /> Delete
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
