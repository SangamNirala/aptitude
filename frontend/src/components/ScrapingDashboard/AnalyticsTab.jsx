import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { useQuery } from '@tanstack/react-query';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { TrendingUp, Database, Zap, CheckCircle, AlertTriangle, Clock } from 'lucide-react';
import { 
  fetchSourceAnalytics, 
  fetchJobAnalytics, 
  fetchPerformanceMetrics, 
  fetchQualityAnalytics,
  fetchTrendAnalysis 
} from '../../services/api';

const MetricCard = ({ title, value, subtitle, icon: Icon, color = "blue", trend }) => {
  const colorClasses = {
    blue: "bg-blue-500/20 border-blue-500/30 text-blue-400",
    green: "bg-green-500/20 border-green-500/30 text-green-400",
    yellow: "bg-yellow-500/20 border-yellow-500/30 text-yellow-400",
    purple: "bg-purple-500/20 border-purple-500/30 text-purple-400",
    red: "bg-red-500/20 border-red-500/30 text-red-400"
  };

  return (
    <Card className={`${colorClasses[color]} backdrop-blur-sm border`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-white/70">{title}</p>
            <div className="flex items-center gap-2">
              <p className="text-2xl font-bold text-white">{value}</p>
              {trend && (
                <span className={`text-sm ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {trend > 0 ? '+' : ''}{trend}%
                </span>
              )}
            </div>
            {subtitle && <p className="text-xs text-white/60 mt-1">{subtitle}</p>}
          </div>
          <Icon className="h-8 w-8 text-white/50" />
        </div>
      </CardContent>
    </Card>
  );
};

const SourcePerformanceChart = ({ data }) => {
  return (
    <Card className="bg-white/10 backdrop-blur-sm border-white/20">
      <CardHeader>
        <CardTitle className="text-white">Source Performance</CardTitle>
        <CardDescription className="text-blue-200">
          Questions extracted per source over time
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip 
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Area 
              type="monotone" 
              dataKey="indiabix" 
              stackId="1"
              stroke="#3B82F6" 
              fill="#3B82F6" 
              fillOpacity={0.3}
              name="IndiaBix"
            />
            <Area 
              type="monotone" 
              dataKey="geeksforgeeks" 
              stackId="1"
              stroke="#10B981" 
              fill="#10B981" 
              fillOpacity={0.3}
              name="GeeksforGeeks"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

const QualityDistributionChart = ({ data }) => {
  const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444'];

  return (
    <Card className="bg-white/10 backdrop-blur-sm border-white/20">
      <CardHeader>
        <CardTitle className="text-white">Quality Distribution</CardTitle>
        <CardDescription className="text-blue-200">
          Distribution of question quality scores
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data?.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px'
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

const TrendAnalysisChart = ({ data }) => {
  return (
    <Card className="bg-white/10 backdrop-blur-sm border-white/20">
      <CardHeader>
        <CardTitle className="text-white">Performance Trends</CardTitle>
        <CardDescription className="text-blue-200">
          Key metrics trending over time
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="period" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip 
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="questions" 
              stroke="#3B82F6" 
              strokeWidth={2}
              name="Questions Processed"
            />
            <Line 
              type="monotone" 
              dataKey="quality_score" 
              stroke="#10B981" 
              strokeWidth={2}
              name="Quality Score"
            />
            <Line 
              type="monotone" 
              dataKey="processing_time" 
              stroke="#F59E0B" 
              strokeWidth={2}
              name="Processing Time (ms)"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

const AnalyticsTab = () => {
  const [timeRange, setTimeRange] = useState('7d');

  const { data: sourceAnalytics } = useQuery({
    queryKey: ['sourceAnalytics'],
    queryFn: fetchSourceAnalytics,
  });

  const { data: jobAnalytics } = useQuery({
    queryKey: ['jobAnalytics'],
    queryFn: fetchJobAnalytics,
  });

  const { data: performanceMetrics } = useQuery({
    queryKey: ['performanceMetrics'],
    queryFn: fetchPerformanceMetrics,
  });

  const { data: qualityAnalytics } = useQuery({
    queryKey: ['qualityAnalytics'],
    queryFn: fetchQualityAnalytics,
  });

  const { data: trendAnalysis } = useQuery({
    queryKey: ['trendAnalysis'],
    queryFn: fetchTrendAnalysis,
  });

  // Mock data for charts - in real app this would come from APIs
  const sourcePerformanceData = [
    { name: 'Mon', indiabix: 45, geeksforgeeks: 32 },
    { name: 'Tue', indiabix: 52, geeksforgeeks: 41 },
    { name: 'Wed', indiabix: 38, geeksforgeeks: 28 },
    { name: 'Thu', indiabix: 61, geeksforgeeks: 47 },
    { name: 'Fri', indiabix: 55, geeksforgeeks: 39 },
    { name: 'Sat', indiabix: 67, geeksforgeeks: 52 },
    { name: 'Sun', indiabix: 43, geeksforgeeks: 35 },
  ];

  const qualityDistributionData = [
    { name: 'Excellent (90-100)', value: 25 },
    { name: 'Good (80-89)', value: 45 },
    { name: 'Fair (70-79)', value: 20 },
    { name: 'Poor (< 70)', value: 10 },
  ];

  const trendData = [
    { period: 'Week 1', questions: 120, quality_score: 82, processing_time: 450 },
    { period: 'Week 2', questions: 145, quality_score: 85, processing_time: 420 },
    { period: 'Week 3', questions: 135, quality_score: 88, processing_time: 380 },
    { period: 'Week 4', questions: 167, quality_score: 86, processing_time: 350 },
    { period: 'Week 5', questions: 189, quality_score: 89, processing_time: 320 },
    { period: 'Week 6', questions: 203, quality_score: 91, processing_time: 310 },
  ];

  return (
    <div className="space-y-6">
      {/* Analytics Header */}
      <Card className="bg-white/10 backdrop-blur-sm border-white/20">
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="text-white">Analytics Dashboard</CardTitle>
              <CardDescription className="text-blue-200">
                Comprehensive insights into your scraping performance
              </CardDescription>
            </div>
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-32 bg-white/10 border-white/20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-600">
                <SelectItem value="24h">Last 24h</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Questions"
          value={performanceMetrics?.total_questions || "1,247"}
          subtitle="All sources combined"
          icon={Database}
          color="blue"
          trend={12}
        />
        
        <MetricCard
          title="Average Quality"
          value={qualityAnalytics?.average_quality_score?.toFixed(1) || "86.5"}
          subtitle="Quality score out of 100"
          icon={CheckCircle}
          color="green"
          trend={5}
        />
        
        <MetricCard
          title="Processing Speed"
          value={performanceMetrics?.avg_processing_time || "340ms"}
          subtitle="Average per question"
          icon={Zap}
          color="yellow"
          trend={-8}
        />
        
        <MetricCard
          title="Success Rate"
          value={jobAnalytics?.success_rate?.toFixed(1) + '%' || "94.2%"}
          subtitle="Job completion rate"
          icon={TrendingUp}
          color="purple"
          trend={3}
        />
      </div>

      {/* Analytics Tabs */}
      <Tabs defaultValue="performance" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 bg-white/10 backdrop-blur-sm">
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="quality">Quality</TabsTrigger>
          <TabsTrigger value="sources">Sources</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SourcePerformanceChart data={sourcePerformanceData} />
            <Card className="bg-white/10 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="text-white">Job Performance</CardTitle>
                <CardDescription className="text-blue-200">
                  Recent job execution metrics
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                  <div>
                    <div className="text-white font-medium">IndiaBix Batch #47</div>
                    <div className="text-sm text-blue-200">Completed 2 hours ago</div>
                  </div>
                  <div className="text-right">
                    <div className="text-white">89 questions</div>
                    <div className="text-sm text-green-400">98.9% success</div>
                  </div>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                  <div>
                    <div className="text-white font-medium">GeeksforGeeks Batch #23</div>
                    <div className="text-sm text-blue-200">Completed 4 hours ago</div>
                  </div>
                  <div className="text-right">
                    <div className="text-white">67 questions</div>
                    <div className="text-sm text-green-400">95.5% success</div>
                  </div>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                  <div>
                    <div className="text-white font-medium">Mixed Sources Batch #12</div>
                    <div className="text-sm text-blue-200">Completed 6 hours ago</div>
                  </div>
                  <div className="text-right">
                    <div className="text-white">124 questions</div>
                    <div className="text-sm text-green-400">91.1% success</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="quality" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <QualityDistributionChart data={qualityDistributionData} />
            <Card className="bg-white/10 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="text-white">Quality Metrics</CardTitle>
                <CardDescription className="text-blue-200">
                  Detailed quality assessment breakdown
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-white">Content Completeness</span>
                    <span className="text-blue-200">92%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{width: '92%'}}></div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-white">Format Accuracy</span>
                    <span className="text-blue-200">89%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{width: '89%'}}></div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-white">Answer Validity</span>
                    <span className="text-blue-200">94%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-purple-500 h-2 rounded-full" style={{width: '94%'}}></div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-white">Duplicate Detection</span>
                    <span className="text-blue-200">97%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-yellow-500 h-2 rounded-full" style={{width: '97%'}}></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="sources">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-white/10 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="text-white">Source Comparison</CardTitle>
                <CardDescription className="text-blue-200">
                  Performance comparison between sources
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={[
                    { name: 'IndiaBix', questions: 847, quality: 88, speed: 340 },
                    { name: 'GeeksforGeeks', questions: 623, quality: 85, speed: 380 }
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="name" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: '#1F2937',
                        border: '1px solid #374151',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Bar dataKey="questions" fill="#3B82F6" name="Questions" />
                    <Bar dataKey="quality" fill="#10B981" name="Quality Score" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="text-white">Source Health</CardTitle>
                <CardDescription className="text-blue-200">
                  Current status and reliability metrics
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {sourceAnalytics?.map((source, index) => (
                  <div key={index} className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                    <div>
                      <div className="text-white font-medium">{source.source_name}</div>
                      <div className="text-sm text-blue-200">Last active: {source.last_activity}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-green-400">{source.success_rate}% uptime</div>
                      <div className="text-xs text-blue-200">{source.total_questions} questions</div>
                    </div>
                  </div>
                )) || [
                  <div className="text-center py-6 text-blue-300">
                    Loading source analytics...
                  </div>
                ]}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="trends">
          <TrendAnalysisChart data={trendData} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AnalyticsTab;