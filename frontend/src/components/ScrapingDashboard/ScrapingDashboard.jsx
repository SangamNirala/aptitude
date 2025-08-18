import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Monitor, BarChart3, Settings, AlertTriangle } from 'lucide-react';
import { useQuery, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import OverviewTab from './OverviewTab';
import JobManagementTab from './JobManagementTab';
import AnalyticsTab from './AnalyticsTab';
import SystemMonitoringTab from './SystemMonitoringTab';
import Navigation from '../Navigation';

// Create a query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchInterval: 30000, // Refetch every 30 seconds
      staleTime: 10000, // Data is fresh for 10 seconds
    },
  },
});

const ScrapingDashboardContent = () => {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-950 via-purple-900 to-indigo-950">
      <Navigation />
      
      <div className="container mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🚀 AI-Enhanced Scraping Dashboard
          </h1>
          <p className="text-blue-200">
            Monitor and manage your intelligent question scraping operations
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-white/10 backdrop-blur-sm">
            <TabsTrigger 
              value="overview" 
              className="flex items-center gap-2 data-[state=active]:bg-white/20"
            >
              <Monitor className="w-4 h-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger 
              value="jobs" 
              className="flex items-center gap-2 data-[state=active]:bg-white/20"
            >
              <Settings className="w-4 h-4" />
              Job Management
            </TabsTrigger>
            <TabsTrigger 
              value="analytics" 
              className="flex items-center gap-2 data-[state=active]:bg-white/20"
            >
              <BarChart3 className="w-4 h-4" />
              Analytics
            </TabsTrigger>
            <TabsTrigger 
              value="monitoring" 
              className="flex items-center gap-2 data-[state=active]:bg-white/20"
            >
              <AlertTriangle className="w-4 h-4" />
              System Monitoring
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <OverviewTab />
          </TabsContent>

          <TabsContent value="jobs">
            <JobManagementTab />
          </TabsContent>

          <TabsContent value="analytics">
            <AnalyticsTab />
          </TabsContent>

          <TabsContent value="monitoring">
            <SystemMonitoringTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

const ScrapingDashboard = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ScrapingDashboardContent />
    </QueryClientProvider>
  );
};

export default ScrapingDashboard;