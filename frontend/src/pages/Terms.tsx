import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';

export const Terms = () => {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 py-8 md:py-12">
        <Link to="/">
          <Button variant="ghost" className="mb-6">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Button>
        </Link>

        <div className="space-y-8">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Terms of Service</h1>
            <p className="text-muted-foreground">Last updated: October 2, 2025</p>
          </div>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Agreement to Terms</h2>
            <p className="text-foreground/80 leading-relaxed">
              By accessing and using this website, you accept and agree to be bound by the terms and 
              provision of this agreement. If you do not agree to these terms, please do not use this service.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Use License</h2>
            <p className="text-foreground/80 leading-relaxed">
              Permission is granted to temporarily access the materials on our website for personal, 
              non-commercial transitory viewing only. This is the grant of a license, not a transfer 
              of title, and under this license you may not modify or copy the materials.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Product Information</h2>
            <p className="text-foreground/80 leading-relaxed">
              We strive to provide accurate product descriptions and pricing. However, we do not warrant 
              that product descriptions, pricing, or other content is accurate, complete, reliable, current, 
              or error-free. We reserve the right to correct any errors or omissions.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Orders and Payment</h2>
            <p className="text-foreground/80 leading-relaxed">
              All orders are subject to acceptance and availability. We reserve the right to refuse or 
              cancel any order for any reason. Payment must be received before order processing. We accept 
              major credit cards and other payment methods as displayed during checkout.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Shipping and Delivery</h2>
            <p className="text-foreground/80 leading-relaxed">
              Delivery times are estimates and not guaranteed. We are not responsible for delays caused 
              by shipping carriers or circumstances beyond our control. Risk of loss and title for items 
              pass to you upon delivery to the carrier.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Returns and Refunds</h2>
            <p className="text-foreground/80 leading-relaxed">
              Products may be returned within 14 days of delivery in original, unopened condition. 
              Refunds will be processed to the original payment method within 7-10 business days of 
              receiving the returned item. Shipping costs are non-refundable.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Warranty</h2>
            <p className="text-foreground/80 leading-relaxed">
              All products come with manufacturer warranties as specified. We are not responsible for 
              warranty claims beyond facilitating the manufacturer's warranty process.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Limitation of Liability</h2>
            <p className="text-foreground/80 leading-relaxed">
              In no event shall our company be liable for any damages (including, without limitation, 
              damages for loss of data or profit, or due to business interruption) arising out of the 
              use or inability to use our service.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Governing Law</h2>
            <p className="text-foreground/80 leading-relaxed">
              These terms shall be governed by and construed in accordance with the laws of the United 
              States, without regard to its conflict of law provisions.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Changes to Terms</h2>
            <p className="text-foreground/80 leading-relaxed">
              We reserve the right to modify these terms at any time. Changes will be effective immediately 
              upon posting. Your continued use of the service after changes constitutes acceptance of the 
              new terms.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Contact Information</h2>
            <p className="text-foreground/80 leading-relaxed">
              For questions about these Terms of Service, please contact us at terms@iphone-store.com 
              or call 1-800-MY-IPHONE.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};
