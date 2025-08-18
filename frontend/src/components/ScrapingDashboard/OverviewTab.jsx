import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { useQuery } from '@tanstack/react-query';
import { Activity, Database, Zap, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { fetchSystemStatus, fetchQueueStatus, fetchProductionHealth } from '../../services/api';

const StatusCard = ({ title, value, subtitle, icon: Icon, color = "blue" }) => {
  const colorClasses = {
    blue: "bg-blue-500/20 border-blue-500/30",
    green: "bg-green-500/20 border-green-500/30",
    yellow: "bg-yellow-500/20 border-yellow-500/30",
    purple: "bg-purple-500/20 border-purple-500/30"
  };

  return (
    <Card className={`${colorClasses[color]} backdrop-blur-sm border`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-white">{title}</CardTitle>
        <Icon className="h-4 w-4 text-white" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-white">{value}</div>
        {subtitle && <p className="text-xs text-blue-200 mt-1">{subtitle}</p>}
      </CardContent>
    </Card>
  );
};

const RecentActivity = ({ activities }) => (
  <Card className="bg-white/10 backdrop-blur-sm border-white/20">
    <CardHeader>
      <CardTitle className="text-white">Recent Activity</CardTitle>
      <CardDescription className="text-blue-200">
        Latest scraping and processing events
      </CardDescription>
    </CardHeader>
    <CardContent className="space-y-3">
      {activities?.slice(0, 5).map((activity, index) => (
        <div key={index} className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
          {activity.type === 'success' && <CheckCircle className="w-4 h-4 text-green-400" />}
          {activity.type === 'warning' && <Clock className="w-4 h-4 text-yellow-400" />}
          {activity.type === 'error' && <AlertCircle className="w-4 h-4 text-red-400" />}
          
          <div className="flex-1 min-w-0">
            <p className="text-sm text-white truncate">{activity.message}</p>
            <p className="text-xs text-blue-200">{activity.timestamp}</p>
          </div>
          
          <Badge variant="outline" className="text-xs">
            {activity.source}
          </Badge>
        </div>
      ))}
      
      {(!activities || activities.length === 0) && (
        <div className="text-center py-6 text-blue-300">
          No recent activity
        </div>
      )}
    </CardContent>
  </Card>
);

const OverviewTab = () => {
  const { data: systemStatus } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: fetchSystemStatus,
    refetchInterval: 5000,
  });

  const { data: queueStatus } = useQuery({
    queryKey: ['queueStatus'],
    queryFn: fetchQueueStatus,
    refetchInterval: 5000,
  });

  const { data: productionHealth } = useQuery({
    queryKey: ['productionHealth'],
    queryFn: fetchProductionHealth,
    refetchInterval: 10000,
  });

  // Mock recent activities - in real app this would come from API
  const recentActivities = [
    {
      type: 'success',
      message: 'IndiaBix scraping job completed - 25 questions processed',
      timestamp: '2 minutes ago',
      source: 'IndiaBix'
    },
    {
      type: 'success', 
      message: 'AI quality assessment completed for GeeksforGeeks batch',
      timestamp: '5 minutes ago',
      source: 'AI Processing'
    },
    {
      type: 'warning',
      message: 'Rate limit reached for GeeksforGeeks - backing off',
      timestamp: '8 minutes ago',
      source: 'GeeksforGeeks'
    },
    {
      type: 'success',
      message: 'Duplicate detection identified 3 duplicate questions',
      timestamp: '12 minutes ago',
      source: 'AI Processing'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Status Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatusCard
          title="Active Jobs"
          value={queueStatus?.active_jobs || 0}
          subtitle={`${queueStatus?.queued_jobs || 0} queued`}
          icon={Activity}
          color="blue"
        />
        
        <StatusCard
          title="Total Questions"
          value={systemStatus?.database?.total_questions || 0}
          subtitle="All sources combined"
          icon={Database}
          color="green"
        />
        
        <StatusCard
          title="AI Services"
          value={productionHealth?.components?.ai_services === 'healthy' ? 'Online' : 'Offline'}
          subtitle="Gemini • Groq • HuggingFace"
          icon={Zap}
          color="purple"
        />
        
        <StatusCard
          title="System Health"
          value={productionHealth?.overall_status === 'healthy' ? 'Healthy' : 'Issues'}
          subtitle={`${productionHealth?.critical_count || 0} critical, ${productionHealth?.warning_count || 0} warnings`}
          icon={CheckCircle}
          color={productionHealth?.overall_status === 'healthy' ? 'green' : 'yellow'}
        />
      </div>

      {/* System Performance Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Resources */}
        <Card className="bg-white/10 backdrop-blur-sm border-white/20">
          <CardHeader>
            <CardTitle className="text-white">System Resources</CardTitle>
            <CardDescription className="text-blue-200">
              Current system resource utilization
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-white">
                <span>CPU Usage</span>
                <span>{productionHealth?.system_metrics?.cpu_percent || 0}%</span>
              </div>
              <Progress 
                value={productionHealth?.system_metrics?.cpu_percent || 0} 
                className="bg-white/10"
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-white">
                <span>Memory Usage</span>
                <span>{productionHealth?.system_metrics?.memory_percent || 0}%</span>
              </div>
              <Progress 
                value={productionHealth?.system_metrics?.memory_percent || 0} 
                className="bg-white/10"
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-white">
                <span>Disk Usage</span>
                <span>{productionHealth?.system_metrics?.disk_percent || 0}%</span>
              </div>
              <Progress 
                value={productionHealth?.system_metrics?.disk_percent || 0} 
                className="bg-white/10"
              />
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <RecentActivity activities={recentActivities} />
      </div>

      {/* Quick Actions */}
      <Card className="bg-white/10 backdrop-blur-sm border-white/20">
        <CardHeader>
          <CardTitle className="text-white">Quick Actions</CardTitle>
          <CardDescription className="text-blue-200">
            Common operations and shortcuts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button className="p-4 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 rounded-lg transition-colors">
              <Database className="w-6 h-6 text-blue-400 mx-auto mb-2" />
              <div className="text-sm text-white">Start IndiaBix Job</div>
            </button>
            
            <button className="p-4 bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 rounded-lg transition-colors">
              <Zap className="w-6 h-6 text-green-400 mx-auto mb-2" />
              <div className="text-sm text-white">Start GeeksforGeeks</div>
            </button>
            
            <button className="p-4 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg transition-colors">
              <Activity className="w-6 h-6 text-purple-400 mx-auto mb-2" />
              <div className="text-sm text-white">Run AI Processing</div>
            </button>
            
            <button className="p-4 bg-yellow-600/20 hover:bg-yellow-600/30 border border-yellow-500/30 rounded-lg transition-colors">
              <AlertCircle className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
              <div className="text-sm text-white">View System Logs</div>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OverviewTab;