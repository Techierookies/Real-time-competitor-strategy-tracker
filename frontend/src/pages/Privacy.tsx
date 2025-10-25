import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';

export const Privacy = () => {
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
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Privacy Policy</h1>
            <p className="text-muted-foreground">Last updated: October 2, 2025</p>
          </div>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Information We Collect</h2>
            <p className="text-foreground/80 leading-relaxed">
              We collect information you provide directly to us, such as when you create an account, 
              make a purchase, or contact customer support. This may include your name, email address, 
              phone number, shipping address, and payment information.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">How We Use Your Information</h2>
            <p className="text-foreground/80 leading-relaxed">
              We use the information we collect to process your orders, communicate with you about 
              products and services, improve our website and customer experience, and comply with 
              legal obligations.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Information Sharing</h2>
            <p className="text-foreground/80 leading-relaxed">
              We do not sell or rent your personal information to third parties. We may share your 
              information with service providers who assist us in operating our website, conducting 
              our business, or servicing you.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Data Security</h2>
            <p className="text-foreground/80 leading-relaxed">
              We implement appropriate security measures to protect your personal information from 
              unauthorized access, alteration, disclosure, or destruction.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Your Rights</h2>
            <p className="text-foreground/80 leading-relaxed">
              You have the right to access, correct, or delete your personal information. You may 
              also object to or restrict certain processing of your data. To exercise these rights, 
              please contact us at privacy@iphone-store.com.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Cookies</h2>
            <p className="text-foreground/80 leading-relaxed">
              We use cookies and similar tracking technologies to track activity on our website and 
              hold certain information to improve and analyze our service.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Changes to This Policy</h2>
            <p className="text-foreground/80 leading-relaxed">
              We may update our Privacy Policy from time to time. We will notify you of any changes 
              by posting the new Privacy Policy on this page and updating the "Last updated" date.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Contact Us</h2>
            <p className="text-foreground/80 leading-relaxed">
              If you have any questions about this Privacy Policy, please contact us at 
              privacy@iphone-store.com or call us at 1-800-MY-IPHONE.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};
