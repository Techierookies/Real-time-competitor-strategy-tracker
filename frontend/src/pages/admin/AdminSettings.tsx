import { useState, useEffect } from 'react';
import { Save, Moon, Sun, Bell, Mail, Shield, CreditCard } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Switch } from '../../components/ui/switch';
import { Separator } from '../../components/ui/separator';
import { useToast } from '../../hooks/use-toast';

export const AdminSettings = () => {
  const { toast } = useToast();
  const [isDark, setIsDark] = useState(false);

  // Apply dark mode globally
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      document.body.style.backgroundColor = '#0f172a';
      document.body.style.color = '#f8fafc';
    } else {
      document.documentElement.classList.remove('dark');
      document.body.style.backgroundColor = '#ffffff';
      document.body.style.color = '#000000';
    }
  }, [isDark]);

  const [settings, setSettings] = useState({
    storeName: 'iPhone Store India',
    storeEmail: 'admin@iphonestore.in',
    currency: 'INR',
    gstRate: '18',
    shippingFee: '500',
    paymentGateway: 'Razorpay',
    emailNotifications: true,
    orderAlerts: true,
    stockAlerts: true,
    marketingEmails: false,
  });

  const handleSave = () => {
    toast({
      title: 'Settings saved',
      description: 'Your changes have been saved successfully.',
    });
  };

  // Styles
  const cardBg = isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-black';
  const subText = isDark ? 'text-gray-400' : 'text-gray-600';
  const switchWrap = isDark
    ? 'rounded-full p-1 bg-gray-700 border border-gray-600'
    : 'rounded-full p-1 bg-gray-200 border border-gray-300';

  return (
    <div
      className={`space-y-6 min-h-screen p-6 transition-all duration-500 ${
        isDark ? 'bg-gray-900 text-white' : 'bg-white text-black'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold">Settings</h1>
          <p className={`${subText} mt-1`}>Manage your store settings and preferences</p>
        </div>

        <Button
          onClick={handleSave}
          className={`${
            isDark ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-gray-800 hover:bg-gray-700 text-white'
          }`}
        >
          <Save className="h-4 w-4 mr-2" />
          Save Changes
        </Button>
      </div>

      <div className="grid gap-6">
        {/* General Settings */}
        <Card className={`border ${cardBg}`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className={`h-5 w-5 ${isDark ? 'text-gray-300' : 'text-gray-700'}`} />
              General Settings
            </CardTitle>
            <CardDescription className={subText}>Basic store information and configuration</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="storeName">Store Name</Label>
                <Input
                  id="storeName"
                  value={settings.storeName}
                  onChange={(e) => setSettings({ ...settings, storeName: e.target.value })}
                  className={`${isDark ? 'bg-gray-700 text-white border-gray-600' : ''}`}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="storeEmail">Store Email</Label>
                <Input
                  id="storeEmail"
                  type="email"
                  value={settings.storeEmail}
                  onChange={(e) => setSettings({ ...settings, storeEmail: e.target.value })}
                  className={`${isDark ? 'bg-gray-700 text-white border-gray-600' : ''}`}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="currency">Currency</Label>
                <Input id="currency" value={settings.currency} disabled className={`${isDark ? 'bg-gray-700 text-white border-gray-600' : ''}`} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="gstRate">GST Rate (%)</Label>
                <Input
                  id="gstRate"
                  type="number"
                  value={settings.gstRate}
                  onChange={(e) => setSettings({ ...settings, gstRate: e.target.value })}
                  className={`${isDark ? 'bg-gray-700 text-white border-gray-600' : ''}`}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="shippingFee">Default Shipping (₹)</Label>
                <Input
                  id="shippingFee"
                  type="number"
                  value={settings.shippingFee}
                  onChange={(e) => setSettings({ ...settings, shippingFee: e.target.value })}
                  className={`${isDark ? 'bg-gray-700 text-white border-gray-600' : ''}`}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="paymentGateway">Payment Gateway</Label>
              <select
                id="paymentGateway"
                value={settings.paymentGateway}
                onChange={(e) => setSettings({ ...settings, paymentGateway: e.target.value })}
                className={`w-full rounded-md border px-3 py-2 ${
                  isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-black'
                }`}
              >
                <option value="Razorpay">Razorpay</option>
                <option value="Paytm">Paytm</option>
                <option value="PhonePe">PhonePe</option>
                <option value="UPI">UPI</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card className={`border ${cardBg}`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {isDark ? <Moon className="h-5 w-5 text-gray-300" /> : <Sun className="h-5 w-5 text-gray-600" />}
              Appearance
            </CardTitle>
            <CardDescription className={subText}>Customize the look and feel of your dashboard</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Dark Mode</Label>
                <p className={`${subText} text-sm`}>Switch between light and dark theme</p>
              </div>
              <div className={`${switchWrap}`}>
                <Switch
                  checked={isDark}
                  onCheckedChange={(checked) => setIsDark(checked)}
                  className="data-[state=checked]:bg-gray-500 data-[state=unchecked]:bg-gray-300"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card className={`border ${cardBg}`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className={`h-5 w-5 ${isDark ? 'text-gray-300' : 'text-gray-700'}`} />
              Notifications
            </CardTitle>
            <CardDescription className={subText}>Manage how you receive notifications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              ['Email Notifications', 'Receive email updates about your store', 'emailNotifications'],
              ['Order Alerts', 'Get notified when new orders are placed', 'orderAlerts'],
              ['Stock Alerts', 'Alert when products are low in stock', 'stockAlerts'],
              ['Marketing Emails', 'Receive tips and updates from our team', 'marketingEmails'],
            ].map(([label, desc, key]) => (
              <div key={label}>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>{label}</Label>
                    <p className={`${subText} text-sm`}>{desc}</p>
                  </div>
                  <div className={`${switchWrap}`}>
                    <Switch
                      checked={settings[key as keyof typeof settings] as boolean}
                      onCheckedChange={(checked) => setSettings({ ...settings, [key]: checked })}
                      className="data-[state=checked]:bg-gray-500 data-[state=unchecked]:bg-gray-300"
                    />
                  </div>
                </div>
                <Separator />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Shipping Configuration */}
        <Card className={`border ${cardBg}`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className={`h-5 w-5 ${isDark ? 'text-gray-300' : 'text-gray-700'}`} />
              Shipping Configuration
            </CardTitle>
            <CardDescription className={subText}>Configure shipping zones and rates for Indian states</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {[
                ['Metro Cities (Mumbai, Delhi, Bangalore, Chennai)', '₹500'],
                ['Tier-1 Cities', '₹750'],
                ['Tier-2 & Tier-3 Cities', '₹1000'],
                ['Remote Areas', '₹1500'],
              ].map(([label, value]) => (
                <div key={label} className="space-y-2">
                  <Label>{label}</Label>
                  <Input defaultValue={value} className={`${isDark ? 'bg-gray-700 text-white border-gray-600' : ''}`} />
                </div>
              ))}
            </div>
            <div className="space-y-2">
              <Label>Free Shipping Threshold (₹)</Label>
              <Input defaultValue="50000" className={`${isDark ? 'bg-gray-700 text-white border-gray-600' : ''}`} />
            </div>
          </CardContent>
        </Card>

        {/* Email Configuration */}
        <Card className={`border ${cardBg}`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className={`h-5 w-5 ${isDark ? 'text-gray-300' : 'text-gray-700'}`} />
              Email Configuration
            </CardTitle>
            <CardDescription className={subText}>Configure email settings for customer communications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>SMTP Host</Label>
                <Input placeholder="smtp.gmail.com" className={`${isDark ? 'bg-gray-700 text-white border-gray-600' : ''}`} />
              </div>
              <div>
                <Label>SMTP Port</Label>
                <Input placeholder="587" className={`${isDark ? 'bg-gray-700 text-white border-gray-600' : ''}`} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>SMTP Username</Label>
                <Input placeholder="your-email@gmail.com" className={`${isDark ? 'bg-gray-700 text-white border-gray-600' : ''}`} />
              </div>
              <div>
                <Label>SMTP Password</Label>
                <Input type="password" placeholder="••••••••" className={`${isDark ? 'bg-gray-700 text-white border-gray-600' : ''}`} />
              </div>
            </div>
            <Button variant="outline" className={`${isDark ? 'bg-gray-700 text-white hover:bg-gray-600' : 'hover:bg-gray-100 text-gray-700'}`}>
              Test Email Configuration
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
