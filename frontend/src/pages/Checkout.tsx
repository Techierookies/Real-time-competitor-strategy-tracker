import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Separator } from "../components/ui/separator";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { CreditCard, Truck, CheckCircle, ArrowLeft } from "lucide-react";

interface CheckoutItem {
  product: any;
  selectedColor: string;
  selectedStorage: string;
  quantity: number;
}

export const Checkout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);

  const checkoutData: CheckoutItem = location.state || {
    product: {
      id: "1",
      name: "iPhone 15 Pro Max",
      price: 140900,
      image: "/iphones/iphone-15.jpeg",
    },
    selectedColor: "Natural Titanium",
    selectedStorage: "256GB",
    quantity: 1,
  };

  const steps = [
    { id: 1, name: "Shipping", icon: Truck },
    { id: 2, name: "Payment", icon: CreditCard },
    { id: 3, name: "Review", icon: CheckCircle },
  ];

  const subtotal = checkoutData.product.price * checkoutData.quantity;
  const shipping = 0;
  const tax = Math.round(subtotal * 0.08);
  const total = subtotal + shipping + tax;

  const formatPrice = (price: number) =>
    price.toLocaleString("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    });

  const handleNext = () => {
    if (currentStep < 3) setCurrentStep(currentStep + 1);
    else {
      setIsProcessing(true);
      setTimeout(() => {
        alert("Order placed successfully!");
        navigate("/");
      }, 2000);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  const progressPercentage = (currentStep / 3) * 100;

  return (
    <div className="container mx-auto px-4 py-10 max-w-5xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-10">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(-1)}
          className="rounded-full hover:bg-muted/60"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="font-display text-4xl md:text-5xl text-center font-bold bg-gradient-to-r from-indigo-600 via-pink-500 to-red-500 bg-clip-text text-transparent ">
          Checkout
        </h1>
      </div>

      {/* Step Indicators */}
      <div className="mb-10">
        <div className="flex justify-between items-center mb-4">
          {steps.map((step) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isCompleted = currentStep > step.id;

            return (
              <div
                key={step.id}
                className={`flex items-center gap-2 px-5 py-2 rounded-full transition-all duration-300 ${
                  isActive
                    ? "bg-black text-white shadow-md"
                    : isCompleted
                    ? "bg-muted text-muted-foreground"
                    : "text-muted-foreground bg-muted/30"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span className="font-medium hidden sm:block">
                  {step.name}
                </span>
              </div>
            );
          })}
        </div>
        <Progress value={progressPercentage} className="h-2 rounded-full" />
      </div>

      <div className="grid lg:grid-cols-3 gap-10">
        {/* Left Section */}
        <div className="lg:col-span-2 space-y-8">
          {/* Step 1: Shipping */}
          {currentStep === 1 && (
            <Card className="p-8 backdrop-blur-sm bg-white/60 shadow-lg border border-gray-200">
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Truck className="h-5 w-5" />
                Shipping Information
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <Label htmlFor="firstName">First Name</Label>
                  <Input id="firstName" placeholder="" />
                </div>
                <div>
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input id="lastName" placeholder="" />
                </div>
                <div className="md:col-span-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" placeholder="" />
                </div>
                <div className="md:col-span-2">
                  <Label htmlFor="address">Address</Label>
                  <Input id="address" placeholder="" />
                </div>
                <div>
                  <Label htmlFor="city">City</Label>
                  <Input id="city" placeholder="" />
                </div>
                <div>
                  <Label htmlFor="pin">Pin Code</Label>
                  <Input id="pin" placeholder="" />
                </div>
              </div>
            </Card>
          )}

          {/* Step 2: Payment */}
          {currentStep === 2 && (
            <Card className="p-8 backdrop-blur-sm bg-white/60 shadow-lg border border-gray-200">
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Payment Details
              </h2>
              <div className="space-y-5">
                <div>
                  <Label htmlFor="cardNumber">Card Number</Label>
                  <Input id="cardNumber" placeholder="1234 5678 9012 3456" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="expiry">Expiry Date</Label>
                    <Input id="expiry" placeholder="MM/YY" />
                  </div>
                  <div>
                    <Label htmlFor="cvv">CVV</Label>
                    <Input id="cvv" placeholder="123" />
                  </div>
                </div>
                <div>
                  <Label htmlFor="cardName">Name on Card</Label>
                  <Input id="cardName" placeholder="John Doe" />
                </div>
              </div>
            </Card>
          )}

          {/* Step 3: Review */}
          {currentStep === 3 && (
            <Card className="p-8 backdrop-blur-sm bg-white/60 shadow-lg border border-gray-200">
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <CheckCircle className="h-5 w-5" />
                Review Your Order
              </h2>
              <div className="space-y-4 text-sm text-muted-foreground">
                <div className="p-4 bg-muted/50 rounded-lg">
                  <h3 className="font-medium text-foreground mb-2">
                    Shipping Address
                  </h3>
                  Bhawana Gupta<br />
                  XYZ<br />
                  Jaipur, 302006
                </div>
                <div className="p-4 bg-muted/50 rounded-lg">
                  <h3 className="font-medium text-foreground mb-2">
                    Payment Method
                  </h3>
                  Visa ending in ••••3456
                </div>
              </div>
            </Card>
          )}

          {/* Buttons */}
          <div className="flex justify-between pt-2">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentStep === 1}
              className="rounded-full px-6"
            >
              Previous
            </Button>
            <Button
              onClick={handleNext}
              disabled={isProcessing}
              className="rounded-full bg-black text-white px-6 hover:bg-gray-800"
            >
              {isProcessing
                ? "Processing..."
                : currentStep === 3
                ? "Place Order"
                : "Next"}
            </Button>
          </div>
        </div>

        {/* Right Section: Order Summary */}
        <Card className="p-6 sticky top-10 bg-white/70 backdrop-blur-sm shadow-lg border border-gray-200">
          <h2 className="text-xl font-semibold mb-5">Order Summary</h2>
          <div className="flex gap-4 mb-5">
            <img
              src={checkoutData.product.image}
              alt={checkoutData.product.name}
              className="w-20 h-20 object-cover rounded-xl"
            />
            <div className="flex-1">
              <h3 className="font-medium">{checkoutData.product.name}</h3>
              <p className="text-sm text-muted-foreground">
                {checkoutData.selectedColor} • {checkoutData.selectedStorage}
              </p>
              <p className="text-sm text-muted-foreground">
                Qty: {checkoutData.quantity}
              </p>
            </div>
            <div className="text-right font-medium">
              {formatPrice(subtotal)}
            </div>
          </div>

          <Separator className="my-4" />

          <div className="space-y-2 mb-5 text-sm">
            <div className="flex justify-between">
              <span>Subtotal</span>
              <span>{formatPrice(subtotal)}</span>
            </div>
            <div className="flex justify-between">
              <span>Shipping</span>
              {shipping === 0 ? (
                <Badge variant="secondary" className="text-xs">
                  Free
                </Badge>
              ) : (
                <span>{formatPrice(shipping)}</span>
              )}
            </div>
            <div className="flex justify-between">
              <span>Tax</span>
              <span>{formatPrice(tax)}</span>
            </div>
          </div>

          <Separator className="my-4" />
          <div className="flex justify-between text-lg font-semibold">
            <span>Total</span>
            <span>{formatPrice(total)}</span>
          </div>
        </Card>
      </div>
    </div>
  );
};
