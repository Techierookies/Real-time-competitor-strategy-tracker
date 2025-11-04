import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Separator } from '../components/ui/separator';
import { 
  MessageCircle, 
  Phone, 
  Mail, 
  Clock, 
  MapPin,
  Headphones,
  Shield,
  Wrench
} from 'lucide-react';

export const Support = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 px-4 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-3 tracking-tight">
          Support Center
        </h1>
        <p className="text-lg text-gray-600">
          We're here to help you with any questions or issues
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-10">
        {/* Left Side */}
        <div className="space-y-8">
          {/* Contact Methods */}
          <Card className="p-6 shadow-lg hover:shadow-xl transition rounded-2xl border border-gray-200 bg-white/90 backdrop-blur-sm">
            <h2 className="text-xl font-semibold text-gray-900 mb-5">Contact Us</h2>
            <div className="space-y-6">
              
              {/* Phone */}
              <div className="flex items-start gap-4">
                <div className="p-3 bg-blue-100 rounded-xl">
                  <Phone className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Phone Support</h3>
                  <p className="text-sm text-gray-600 mb-1">1-800-APL-CARE</p>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Clock className="h-3 w-3" />
                    <span>Mon-Sun: 8am - 8pm</span>
                  </div>
                </div>
              </div>

              <Separator className="bg-gradient-to-r from-gray-200 to-transparent" />

              {/* Live Chat */}
              <div className="flex items-start gap-4">
                <div className="p-3 bg-green-100 rounded-xl">
                  <MessageCircle className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Live Chat</h3>
                  <p className="text-sm text-gray-600 mb-2">Chat with our support team</p>
                  <Button size="sm" className="rounded-xl bg-green-600 hover:bg-green-700 text-white">
                    Start Chat
                  </Button>
                </div>
              </div>

              <Separator className="bg-gradient-to-r from-gray-200 to-transparent" />

              {/* Email */}
              <div className="flex items-start gap-4">
                <div className="p-3 bg-purple-100 rounded-xl">
                  <Mail className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Email Support</h3>
                  <p className="text-sm text-gray-600">support@iphonestore.com</p>
                  <p className="text-xs text-gray-500">Response within 24 hours</p>
                </div>
              </div>

              <Separator className="bg-gradient-to-r from-gray-200 to-transparent" />

              {/* Stores */}
              <div className="flex items-start gap-4">
                <div className="p-3 bg-pink-100 rounded-xl">
                  <MapPin className="h-6 w-6 text-pink-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Store Locations</h3>
                  <p className="text-sm text-gray-600 mb-2">Visit us in person</p>
                  <Button variant="outline" size="sm" className="rounded-xl border-pink-300 hover:bg-pink-50">
                    Find Stores
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {/* Quick Help */}
          <Card className="p-6 shadow-lg hover:shadow-xl transition rounded-2xl border border-gray-200 bg-white/90 backdrop-blur-sm">
            <h2 className="text-xl font-semibold text-gray-900 mb-5">Quick Help</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Button className="h-auto p-5 flex flex-col items-center gap-3 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700">
                <Headphones className="h-7 w-7" />
                <span className="text-sm font-medium">Technical</span>
              </Button>
              <Button className="h-auto p-5 flex flex-col items-center gap-3 rounded-xl bg-yellow-50 hover:bg-yellow-100 text-yellow-700">
                <Shield className="h-7 w-7" />
                <span className="text-sm font-medium">Warranty</span>
              </Button>
              <Button className="h-auto p-5 flex flex-col items-center gap-3 rounded-xl bg-red-50 hover:bg-red-100 text-red-700">
                <Wrench className="h-7 w-7" />
                <span className="text-sm font-medium">Repairs</span>
              </Button>
            </div>
          </Card>
        </div>

        {/* Contact Form */}
        <Card className="p-6 shadow-lg hover:shadow-xl transition rounded-2xl border border-gray-200 bg-white/90 backdrop-blur-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-5">Send us a Message</h2>
          <form className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="firstName">First Name</Label>
                <Input id="firstName" placeholder="John" className="rounded-xl" />
              </div>
              <div>
                <Label htmlFor="lastName">Last Name</Label>
                <Input id="lastName" placeholder="Doe" className="rounded-xl" />
              </div>
            </div>
            
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="john.doe@example.com" className="rounded-xl" />
            </div>
            
            <div>
              <Label htmlFor="subject">Subject</Label>
              <Input id="subject" placeholder="How can we help you?" className="rounded-xl" />
            </div>
            
            <div>
              <Label htmlFor="message">Message</Label>
              <Textarea 
                id="message" 
                placeholder="Please describe your issue or question..."
                rows={5}
                className="rounded-xl"
              />
            </div>
            
            <Button className="w-full rounded-xl bg-blue-600 hover:bg-blue-700 text-white">
              Send Message
            </Button>
          </form>
        </Card>
      </div>

      {/* FAQ */}
      <Card className="p-6 mt-12 shadow-lg hover:shadow-xl transition rounded-2xl border border-gray-200 bg-white/90 backdrop-blur-sm">
        <h2 className="text-xl font-semibold text-gray-900 mb-5">Frequently Asked Questions</h2>
        <div className="space-y-6">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">How can I track my order?</h3>
            <p className="text-sm text-gray-600">
              You can track your order using the tracking number sent to your email after purchase.
            </p>
          </div>
          <Separator />
          <div>
            <h3 className="font-medium text-gray-900 mb-2">What is your return policy?</h3>
            <p className="text-sm text-gray-600">
              We offer a 14-day return policy for all unopened items in original packaging.
            </p>
          </div>
          <Separator />
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Do you offer international shipping?</h3>
            <p className="text-sm text-gray-600">
              Yes, we ship to over 50 countries worldwide. Shipping costs vary by location.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};
