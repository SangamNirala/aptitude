import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Activity, AlertTriangle, CheckCircle, XCircle, Server, 
  Database, Zap, Cpu, HardDrive, Wifi, RefreshCw, Play 
} from 'lucide-react';
import { 
  fetchProductionHealth, 
  fetchProductionMetrics, 
  fetchErrorsDashboard,
  runPerformanceTest,
  runAllHealthChecks,
  fetchSystemHealthAnalytics
} from '../../services/api';

const HealthStatusBadge = ({ status }) => {
  const statusConfig = {
    healthy: { color: 'bg-green-500/20 text-green-400 border-green-500/30', icon: CheckCircle },
    warning: { color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', icon: AlertTriangle },
    critical: { color: 'bg-red-500/20 text-red-400 border-red-500/30', icon: XCircle },
    unknown: { color: 'bg-gray-500/20 text-gray-400 border-gray-500/30', icon: XCircle }
  };

  const config = statusConfig[status?.toLowerCase()] || statusConfig.unknown;
  const IconComponent = config.icon;

  return (
    <Badge className={`${config.color} border flex items-center gap-1`}>
      <IconComponent className="w-3 h-3" />
      {status}
    </Badge>
  );
};

const SystemResourceCard = ({ title, icon: Icon, percentage, details, color = "blue" }) => {
  const colorClasses = {
    blue: "bg-blue-500/20 border-blue-500/30",
    green: "bg-green-500/20 border-green-500/30",
    yellow: "bg-yellow-500/20 border-yellow-500/30",
    red: "bg-red-500/20 border-red-500/30"
  };

  const getProgressColor = (value) => {
    if (value < 60) return "bg-green-500";
    if (value < 80) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <Card className={`${colorClasses[color]} backdrop-blur-sm border`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Icon className="w-5 h-5 text-white" />
            <span className="text-white font-medium">{title}</span>
          </div>
          <span className="text-white font-bold">{percentage}%</span>
        </div>
        
        <div className="space-y-2">
          <Progress 
            value={percentage} 
            className={`bg-white/10`}
          />
          {details && (
            <div className="text-xs text-white/70">
              {details}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const ComponentHealthCard = ({ title, components }) => (
  <Card className="bg-white/10 backdrop-blur-sm border-white/20">
    <CardHeader>
      <CardTitle className="text-white flex items-center gap-2">
        <Server className="w-5 h-5" />
        {title}
      </CardTitle>
      <CardDescription className="text-blue-200">
        Component health status and monitoring
      </CardDescription>
    </CardHeader>
    <CardContent className="space-y-3">
      {Object.entries(components || {}).map(([component, status]) => (
        <div key={component} className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
          <div className="flex items-center gap-3">
            {component === 'database' && <Database className="w-4 h-4 text-blue-400" />}
            {component === 'ai_services' && <Zap className="w-4 h-4 text-purple-400" />}
            {component === 'system_resources' && <Activity className="w-4 h-4 text-green-400" />}
            {component === 'error_tracking' && <AlertTriangle className="w-4 h-4 text-yellow-400" />}
            
            <div>
              <div className="text-white font-medium capitalize">
                {component.replace('_', ' ')}
              </div>
              <div className="text-xs text-blue-200">
                {component === 'database' && 'MongoDB connectivity'}
                {component === 'ai_services' && 'Gemini • Groq • HuggingFace'}
                {component === 'system_resources' && 'CPU • Memory • Disk'}
                {component === 'error_tracking' && 'Error monitoring system'}
              </div>
            </div>
          </div>
          
          <HealthStatusBadge status={status} />
        </div>
      ))}
    </CardContent>
  </Card>
);

const ErrorDashboard = ({ errorData }) => (
  <Card className="bg-white/10 backdrop-blur-sm border-white/20">
    <CardHeader>
      <CardTitle className="text-white flex items-center gap-2">
        <AlertTriangle className="w-5 h-5" />
        Error Dashboard
      </CardTitle>
      <CardDescription className="text-blue-200">
        Recent errors and system alerts
      </CardDescription>
    </CardHeader>
    <CardContent className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-3 bg-red-500/10 rounded-lg border border-red-500/30">
          <div className="text-2xl font-bold text-red-400">
            {errorData?.total_unique_errors || 0}
          </div>
          <div className="text-xs text-red-300">Unique Errors</div>
        </div>
        
        <div className="text-center p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
          <div className="text-2xl font-bold text-yellow-400">
            {errorData?.recent_errors_1h || 0}
          </div>
          <div className="text-xs text-yellow-300">Last Hour</div>
        </div>
        
        <div className="text-center p-3 bg-blue-500/10 rounded-lg border border-blue-500/30">
          <div className="text-2xl font-bold text-blue-400">
            {errorData?.total_occurrences || 0}
          </div>
          <div className="text-xs text-blue-300">Total Events</div>
        </div>
        
        <div className="text-center p-3 bg-purple-500/10 rounded-lg border border-purple-500/30">
          <div className="text-2xl font-bold text-purple-400">
            {errorData?.error_rate_1h?.toFixed(1) || 0}%
          </div>
          <div className="text-xs text-purple-300">Error Rate</div>
        </div>
      </div>

      {errorData?.recent_errors && errorData.recent_errors.length > 0 ? (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {errorData.recent_errors.map((error, index) => (
            <Alert key={index} className="bg-red-500/10 border-red-500/30">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle className="text-red-400">
                {error.category || 'System Error'}
              </AlertTitle>
              <AlertDescription className="text-red-300">
                {error.message}
                <div className="text-xs text-red-400 mt-1">
                  {error.timestamp}
                </div>
              </AlertDescription>
            </Alert>
          ))}
        </div>
      ) : (
        <div className="text-center py-6 text-green-400">
          ✅ No recent errors - System running smoothly
        </div>
      )}
    </CardContent>
  </Card>
);

const SystemMonitoringTab = () => {
  const [isRunningTest, setIsRunningTest] = useState(false);
  const queryClient = useQueryClient();

  const { data: productionHealth, isLoading: healthLoading } = useQuery({
    queryKey: ['productionHealth'],
    queryFn: fetchProductionHealth,
    refetchInterval: 10000,
  });

  const { data: productionMetrics } = useQuery({
    queryKey: ['productionMetrics'],
    queryFn: fetchProductionMetrics,
    refetchInterval: 5000,
  });

  const { data: errorsDashboard } = useQuery({
    queryKey: ['errorsDashboard'],
    queryFn: fetchErrorsDashboard,
    refetchInterval: 15000,
  });

  const { data: systemHealth } = useQuery({
    queryKey: ['systemHealthAnalytics'],
    queryFn: fetchSystemHealthAnalytics,
    refetchInterval: 10000,
  });

  const performanceTestMutation = useMutation({
    mutationFn: runPerformanceTest,
    onMutate: () => setIsRunningTest(true),
    onSettled: () => setIsRunningTest(false),
  });

  const healthCheckMutation = useMutation({
    mutationFn: runAllHealthChecks,
    onSuccess: () => {
      queryClient.invalidateQueries(['productionHealth']);
    },
  });

  const handleRunPerformanceTest = () => {
    performanceTestMutation.mutate();
  };

  const handleRunHealthChecks = () => {
    healthCheckMutation.mutate();
  };

  const handleRefreshAll = () => {
    queryClient.invalidateQueries();
  };

  return (
    <div className="space-y-6">
      {/* Monitoring Header */}
      <Card className="bg-white/10 backdrop-blur-sm border-white/20">
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="text-white">System Monitoring</CardTitle>
              <CardDescription className="text-blue-200">
                Real-time system health and performance monitoring
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefreshAll}
                className="border-white/20"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRunHealthChecks}
                disabled={healthCheckMutation.isLoading}
                className="border-white/20"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Health Check
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRunPerformanceTest}
                disabled={isRunningTest}
                className="border-white/20"
              >
                <Play className="w-4 h-4 mr-2" />
                {isRunningTest ? 'Testing...' : 'Performance Test'}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* System Status Overview */}
      <Card className="bg-white/10 backdrop-blur-sm border-white/20">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Activity className="w-5 h-5" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
            <div>
              <div className="text-2xl font-bold text-white">
                Overall System Health
              </div>
              <div className="text-blue-200">
                {productionHealth?.critical_count || 0} critical • {productionHealth?.warning_count || 0} warnings
              </div>
            </div>
            <HealthStatusBadge status={productionHealth?.overall_status || 'unknown'} />
          </div>
        </CardContent>
      </Card>

      {/* System Resources */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <SystemResourceCard
          title="CPU Usage"
          icon={Cpu}
          percentage={productionMetrics?.cpu_percent || 0}
          details={`Load: ${productionMetrics?.load_average?.[0]?.toFixed(2) || 'N/A'}`}
          color={productionMetrics?.cpu_percent > 80 ? 'red' : productionMetrics?.cpu_percent > 60 ? 'yellow' : 'green'}
        />
        
        <SystemResourceCard
          title="Memory Usage"
          icon={HardDrive}
          percentage={productionMetrics?.memory_percent || 0}
          details="Available memory monitoring"
          color={productionMetrics?.memory_percent > 80 ? 'red' : productionMetrics?.memory_percent > 60 ? 'yellow' : 'green'}
        />
        
        <SystemResourceCard
          title="Disk Usage"
          icon={Database}
          percentage={productionMetrics?.disk_percent || 0}
          details="Storage space utilization"
          color={productionMetrics?.disk_percent > 80 ? 'red' : productionMetrics?.disk_percent > 60 ? 'yellow' : 'green'}
        />
        
        <SystemResourceCard
          title="Network I/O"
          icon={Wifi}
          percentage={Math.min((productionMetrics?.network_io_mb?.total || 0), 100)}
          details="Network activity"
          color="blue"
        />
      </div>

      {/* Component Health and Error Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ComponentHealthCard
          title="Component Health"
          components={productionHealth?.components}
        />
        
        <ErrorDashboard errorData={errorsDashboard} />
      </div>

      {/* System Metrics Details */}
      <Card className="bg-white/10 backdrop-blur-sm border-white/20">
        <CardHeader>
          <CardTitle className="text-white">System Metrics</CardTitle>
          <CardDescription className="text-blue-200">
            Detailed system performance metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="space-y-3">
              <h4 className="text-white font-medium">Resource Utilization</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-blue-200">
                  <span>Active Connections:</span>
                  <span className="text-white">{productionMetrics?.active_connections || 0}</span>
                </div>
                <div className="flex justify-between text-blue-200">
                  <span>Uptime:</span>
                  <span className="text-white">{productionMetrics?.uptime_hours?.toFixed(1) || 0}h</span>
                </div>
                <div className="flex justify-between text-blue-200">
                  <span>Last Check:</span>
                  <span className="text-white">{new Date().toLocaleTimeString()}</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-white font-medium">Performance</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-blue-200">
                  <span>Avg Response:</span>
                  <span className="text-white">{systemHealth?.avg_response_time || 'N/A'}ms</span>
                </div>
                <div className="flex justify-between text-blue-200">
                  <span>Throughput:</span>
                  <span className="text-white">{systemHealth?.throughput || 'N/A'} req/s</span>
                </div>
                <div className="flex justify-between text-blue-200">
                  <span>Success Rate:</span>
                  <span className="text-white">{systemHealth?.success_rate || 'N/A'}%</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-white font-medium">Health Status</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-blue-200">
                  <span>Services Online:</span>
                  <span className="text-white">
                    {Object.values(productionHealth?.components || {}).filter(s => s === 'healthy').length}/
                    {Object.keys(productionHealth?.components || {}).length}
                  </span>
                </div>
                <div className="flex justify-between text-blue-200">
                  <span>Error Rate:</span>
                  <span className="text-white">{errorsDashboard?.error_rate_1h?.toFixed(2) || 0}%</span>
                </div>
                <div className="flex justify-between text-blue-200">
                  <span>Last Error:</span>
                  <span className="text-white">{errorsDashboard?.recent_errors?.[0]?.timestamp || 'None'}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Test Results */}
      {performanceTestMutation.isSuccess && (
        <Card className="bg-green-500/10 border-green-500/30 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-green-400">Performance Test Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-green-300">Test Duration</div>
                <div className="text-white font-bold">
                  {performanceTestMutation.data?.test_duration || 'N/A'}s
                </div>
              </div>
              <div>
                <div className="text-green-300">Performance Score</div>
                <div className="text-white font-bold">
                  {performanceTestMutation.data?.performance_score || 'N/A'}/100
                </div>
              </div>
              <div>
                <div className="text-green-300">Status</div>
                <div className="text-white font-bold">
                  {performanceTestMutation.data?.status || 'Completed'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SystemMonitoringTab;